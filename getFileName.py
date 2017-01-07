# coding=utf-8

import re
import os
import urllib
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TCON, TRCK, APIC, USLT
import pandas as pd
import webbrowser

# DC TALK-Consume me
#Album Photograph Ed Sheeran <code>...
#quitar puntos y tildes nombr de entrada
#read first if there is a cover img
#verify any output to be an html tag
#Change &amp; by &

def remAccents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str) #unicode(,'utf-8')
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def getLyrics(artist,song):
	artist=cleanBasic(artist)
	song=cleanBasic(song)
	
	page=urllib.urlopen('https://www.musixmatch.com/search/'+artist+' '+song).read()
	i=page.find('"track_share_url":"')+len('"track_share_url":"')
	f=page.find('"',i)
	try:
		page=urllib.urlopen(page[i:f]).read()
	except:
		return None
	i=page.find('"body":"')+len('"body":"')
	f=page.find('","language":"')
	lyrics=page[i:f]
	return lyrics.replace('\\n','\n')

def cleanBasic(fname):
	return ''.join([i for i in fname if i not in '/\:*?"<>|'])
	
def cleanFileName(fname):
	'''Remove bad signs and words from file name'''
	fname=fname.decode('cp1252').encode('utf-8')
	k='Victor manuelle-Apiádate de mí.mp3'
	fname=fname[:-3]#removes.mp3
	badSign="'?.%&!|<>-/,\\+*:"+'"' 
	badWords=[' sub. ', 'subtitulado','subtitulada', 'lyrics', ' video','hd','official', 'vevo','amv', 'con letra', 'download', 'wlyrics']
	fname=''.join([i if i not in badSign else ' ' for i in fname]) #Remove bad signs
	fname=re.sub(r'\([^()]*\)', '', fname) #Remove words within parenthesess
	fname=' '.join(filter(lambda x: x.lower() not in badWords, fname.split())) #Remove bad words
	fname='+'.join(fname.split())
	return fname.strip()
	
def attachTags(fname,info,genre,lyrics):
	'''Attach Metadata to file'''
	for i in list(info.index): info[i]=info[i].decode('utf-8').replace('&amp;','&')
	lyrics=lyrics.decode('utf-8')
	try: 
		tags = ID3(fname,v2_version=3)
	except ID3NoHeaderError:
		print "Adding ID3 header;",
		tags = ID3()
	tags["TIT2"] = TIT2(encoding=3, text=info['Name'])
	tags["TALB"] = TALB(encoding=3, text=info['Album'])
	tags["TPE1"] = TPE1(encoding=3, text=info['Band'])
	tags["TCON"] = TCON(encoding=3, text=genre)
	tags["TRCK"] = TRCK(encoding=3, text=info['Track'])
	newName=cleanBasic(info['Name'])
	if lyrics:
		tags["USLT"] = USLT(encoding=3, desc=u'desc', text=lyrics)
		text_file = open(newName+".txt", "w")
		lyrics=lyrics.encode('cp1252')
		text_file.write(lyrics)
	else:
		print 'No Lyrics Available'
	try:
		tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover',data=open(newName+'.jpg','rb').read())
	except: pass
	tags.save(fname,v2_version=3,v1=2)
	
def getFileName():
	'''Gets the name of a mp3 File'''
	fileList=os.listdir(r'C:\Users\Camilo\Documents\py\Proyectos\MusicProyect\mp3Files')
	savedPath=os.getcwd()
	print 'Searching mp3 files in ' + savedPath
	os.chdir(r'C:\Users\Camilo\Documents\py\Proyectos\MusicProyect\mp3Files')
	
	for fileName in fileList:
		if '.mp3' in fileName: 
			archName=fileName
			fileName=cleanFileName(fileName)
			page=getPage(fileName,0) #Replace blanc spaces to + sign
			info,genre=getResults(page,5)
			genre=genre.decode('utf-8')
			lyrics=getLyrics(info['Band'],info['Name'])
			attachTags(archName,info,genre,lyrics)
			fname=cleanBasic(info['Name'])
			os.rename(archName,fname+'.mp3')
			
def getTable(page):
	'''Returns info whitin results table MusicBrainz'''
	return [page.find('<tbody>'),page.find('</tbody>')]
		
def getPage(song,t):
	'''get the results page for a song File Name in MusicBrainz'''
	page=urllib.urlopen('https://musicbrainz.org/search?query='+song+'&type=recording&method=indexed').read()
	print 'Try '+str(t)
	if page.find('Search Error - MusicBrainz')> -1 : 
		t+=1
		return getPage(song,t)
	return page[getTable(page)[0]:getTable(page)[1]]

def getResults(page,initResult):
	'''Print 5 results, user can beg for more'''
	print "Choose the correct one: "
	i=0
	f=0
	rotules=['Name','Band','Album','Track','UrlAlbum','UrlSong']
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
				genres=getThumbandGenre(results.iloc[index][4],results.iloc[index][5],results.iloc[index][0])
				return results.iloc[index],genres
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
	base=page.find('<a href="/recording/',init)+len('<a href="')
	
	urlSong=page[base:page.find('"',base)]
	name,f=getInfo(page,base,'<bdi>')
	band,f=getInfo(page,f,'<bdi>')
	urlAlbum,f=getInfo(page,f,'<a href="')
	album,f=getInfo(page,f,'<bdi>')
	track,f=getInfo(page,f,'<td>')
		
	return name, band, album, track, urlAlbum,urlSong,f

def getThumbandGenre(urlAlbum,urlSong,name):
	'''search and download Thumbnail'''
	pg=urllib.urlopen('https://musicbrainz.org'+urlAlbum).read()
	newName=cleanBasic(name).decode('utf-8')
	if pg.find('<div class="cover-art">')!=-1:
		i=pg.find('<div class="cover-art">')+len('<div class="cover-art">')
		i=pg.find('//',i)+len('//')
		f=pg.find('"',i)
		if '.jpg' in pg[i:f]:
			urllib.urlretrieve('https://'+pg[i:f],newName+'.jpg')#search for invalid names 
		else: print 'No front cover image available'
	'''search and get genre'''
	pg=urllib.urlopen('https://musicbrainz.org'+urlSong+'/tags').read()
	pg,f=getInfo(pg,0,'<div id="all-tags">')
	genre=''
	i=0
	
	while pg.find('<bdi>',i)!=-1:
		aux,i=getInfo(pg,i,'<bdi>')
		genre+=aux+'-'
	if not genre:
		genre=raw_input('No genre available, input desire: ')
		return genre
	return genre[:-1]

#print cleanFileName('Victor manuelle-Apiádate de mí.mp3')
getFileName()