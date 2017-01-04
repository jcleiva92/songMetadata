import re
import os
import urllib
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TCON, TRCK, APIC
import pandas as pd

def cleanFileName(fname):
	'''Remove bad signs and words from file name'''
	fname=fname[:-3]#removes.mp3
	badSign="'?.%&!|<>-/,\\*:"+'"' 
	badWords=[' sub. ', 'subtitulado','subtitulada', 'lyrics', ' video','hd','official', 'vevo','amv']
	fname=''.join([i for i in fname if i not in badSign]) #Remove bad signs
	fname=re.sub(r'\([^()]*\)', '', fname) #Remove words within parenthesess
	fname=' '.join(filter(lambda x: x.lower() not in badWords, fname.split())) #Remove bad words
	
	return fname.strip()
	
def attachTags(fname,info,genre):
	'''Attach Metadata to file'''
	try: 
		tags = ID3(fname,v2_version=3)
	except ID3NoHeaderError:
		print "Adding ID3 header;",
		tags = ID3()
	tags["TIT2"] = TIT2(encoding=3, text=info['Name'])
	tags["TALB"] = TALB(encoding=3, text=info['Album'])
	tags["TPE1"] = TPE1(encoding=3, text=info['Name'])
	tags["TCON"] = TCON(encoding=3, text=genre)
	tags["TRCK"] = TRCK(encoding=3, text=info['Track'])
	tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover',data=open(info['Name']+'.jpg','rb').read())

	tags.save(fname,v2_version=3,v1=2)
	
def get_FileName():
	'''Gets the name of a mp3 File'''
	file_list=os.listdir(r'C:\Users\Camilo\Documents\py\Proyectos\MusicProyect\mp3Files')
	savedPath=os.getcwd()
	print 'Searching mp3 files in ' + savedPath
	os.chdir(r'C:\Users\Camilo\Documents\py\Proyectos\MusicProyect\mp3Files')
	
	for file_name in file_list:
		if '.mp3' in file_name: 
			print file_name
			archName=file_name
			page=getPage('+'.join(cleanFileName(file_name).split())) #Replace blanc spaces to + sign
			info,genre=getResults(page,5)
			attachTags(archName,info,genre)
			os.rename(archName,info['Name']+'.mp3')
			
def getTable(page):
	'''Returns info whitin results table MusicBrainz'''
	return [page.find('<tbody>'),page.find('</tbody>')]
		
def getPage(song):
	'''get the results page for a song File Name in MusicBrainz'''
	page=urllib.urlopen('https://musicbrainz.org/search?query='+song+'&type=recording&method=indexed').read()
	#Search Error - MusicBrainz
	return page[getTable(page)[0]:getTable(page)[1]]
	

def getResults(page,initResult):
	'''Print 5 results, user can beg for more'''
	print "Choose the correct one: "
	i=0
	f=0
	rotules=['Name','Band','Album','Track','Url']
	results=pd.DataFrame()
	while i <initResult:
		data=list(getData(page,f))
		f=data[-1]
		results=results.append(pd.DataFrame([data[:-1]],columns=rotules),ignore_index=True)
		i+=1
		if i==initResult: 
			print results.tail(5).ix[:,:4]
			if 'y' in raw_input("More Options? Y/N ").lower(): initResult+=5
			else: 
				index=raw_input("Option Number? ")#validar ingreso de parametros
				index=checkInput(len(results),index)
				tags=getThumbandGenre(results.iloc[index][4],results.iloc[index][0])
				return results.iloc[index],tags
	return None

def checkInput(size,index):
	'''Checks for invalid Input'''
	val=False
	try: 
		index=int(index)
	except: val=True
	if index>size-1 or index<0 or val:
		index=raw_input("Error, Option Number should be between 0 and "+str(size-1)+": ")
		return checkInput(size,index)
	return index
	
def getInfo(page,base,tag):
	'''get string between html tags'''
	i=page.find(tag,base)+len(tag)#si page.find=-1 khe
	if tag=='<a href="':
		f=page.find('">',i)
	elif tag=='<div id="all-tags">':
		f=page.find('</div>',i)
		page=page[i:f]
		return page,len(page)
	else:
		f=page.find(tag[:1]+'/'+tag[1:],i)
	return page[i:f],f
	
def getData(page,init):
	'''Calls getInfo and return the tags results'''
	base=page.find('<a href="/recording/',init)
	
	name,f=getInfo(page,base,'<bdi>')
	band,f=getInfo(page,f,'<bdi>')
	url,f=getInfo(page,f,'<a href="')
	album,f=getInfo(page,f,'<bdi>')
	track,f=getInfo(page,f,'<td>')
		
	return name, band, album, track, url,f

def getThumbandGenre(url,name):
	'''search and download Thumbnail'''
	pg=urllib.urlopen('https://musicbrainz.org'+url).read()
	i=pg.find('data-small-thumbnail="')+len('data-small-thumbnail="')
	f=pg.find('"',i)
	urllib.urlretrieve('https://'+pg[i+2:f],name+'.jpg')#search for invalid names 
	'''search and get genre'''
	pg=urllib.urlopen('https://musicbrainz.org'+url+'/tags').read()
	pg,f=getInfo(pg,0,'<div id="all-tags">')
	genre=''
	i=0
	while pg.find('<bdi>',i)!=-1:
		aux,i=getInfo(pg,i,'<bdi>')
		genre+=aux+'-'
	return genre[:-1]
	
get_FileName()