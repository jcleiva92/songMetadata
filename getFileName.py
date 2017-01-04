import re
import os
import urllib
from mutagen.easyid3 import EasyID3
import pandas as pd

def cleanFileName(fname):
	fname=fname[:-3]#removes.mp3
	badSign="'?.%&!|<>/,\\*:"+'"'
	badWords=[' sub. ', 'subtitulado','subtitulada', 'lyrics', ' video','hd','official', 'vevo','amv']
	fname=''.join([i for i in fname if i not in badSign])
	fname=re.sub(r'\([^()]*\)', '', fname)
	fname=' '.join(filter(lambda x: x.lower() not in badWords, fname.split()))
	return fname.strip()
	
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
			page=getPage('+'.join(cleanFileName(file_name).split()))
			info,tags=getResults(page,5)
			audio=EasyID3(archName)
			audio['title']=info['Name']
			audio['album']=info['Album']
			audio['tracknumber']=info['Track']
			audio['artist']=info['Band']
			audio['genre']=tags
			audio.save()
			os.rename(archName,info['Name']+'.mp3')
			
def getTable(page):
	return [page.find('<tbody>'),page.find('</tbody>')]
		
def getPage(song):
	'''get the results page for a song File Name in MusicBrainz'''
	page=urllib.urlopen('https://musicbrainz.org/search?query='+song+'&type=recording&method=indexed').read()
	return page[getTable(page)[0]:getTable(page)[1]]
	

def getResults(page,initResult):
	print "Choose the correct one: "
	i=0
	f=0
	rotules=['Name','Band','Album','Track','Url']
	results=pd.DataFrame()
	while i <initResult:
		data=list(getData(page,f))
		f=data[-1]
		results=results.append(pd.DataFrame([data[:-1]],columns=rotules),ignore_index=True)
		#Calls after decide which option
		i+=1
		if i==initResult: 
			print results.tail(5).ix[:,:4]
			if 'y' in raw_input("Desea ver mas opciones? Y/N ").lower(): initResult+=5
			else: 
				index=int(raw_input("Cual opcion elige? "))#validar ingreso de parametros
				tags=getThumbandGenre(results.iloc[index][4],results.iloc[index][0])
				return results.iloc[index],tags
	return None
		
def getInfo(page,base,tag):
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