#!/usr/bin/env python

from library import web
import os, os.path, datetime
from library.tmdb import tmdb
from library.tvdb import tvdb_api as tvdb
import peewee as pw

import library.pyacoustid.acoustid as acoustid
import musicbrainz2.webservice as ws

from config import *


MUSIC_FILES=['.mp3','.m4a','.m4p','.mp4','.wav']

database = pw.MySQLDatabase(MySQLDatabase, user=MySQLUser, passwd=MySQLPassword)
database.connect()
class BaseModel(pw.Model):
	class Meta:
			database = database

class Videos(BaseModel):
	id = pw.IntegerField(db_index=True,unique=True)
	filename = pw.CharField(unique=True)
	type = pw.IntegerField(size=2)
	title = pw.CharField()
	date = pw.DateTimeField()
	rating = pw.IntegerField()
	runtime = pw.IntegerField()
	tagline = pw.TextField()
	summary = pw.TextField()
	budget = pw.IntegerField()
	revenue = pw.IntegerField()
	cachedate = pw.DateTimeField()

class Songs(BaseModel):
	id = pw.IntegerField(db_index=True,unique=True)
	filename = pw.CharField(unique=True)
	title = pw.CharField()
	artist = pw.CharField()
	musicbrainz = pw.CharField()

class Tracks(BaseModel):
	trackid = pw.CharField(unique=True, size=36)
	title = pw.CharField()
	artistid = ForeignKeyField(Artists)
	duration = pw.IntegerField()
	
class Releases(BaseModel):
	releaseid = pw.CharField(unique=True, size=36)
	title = pw.CharField()
	artistid = ForeignKeyField(Artists)

class ReleaseTracks(BaseModel):
	trackid = ForeignKeyField(Tracks)
	releaseid = ForeignKeyField(Releases)

class ReleaseEvents(BaseModel):
	releaseid = ForeignKeyField(Releases)
	country = pw.CharField()
	date = pw.DateTimeField()

class Artists(BaseModel):
	artistid = pw.CharField(unique=True, size=36)
	name = pw.CharField()
	disambiguation = pw.CharField()
	startdate = pw.DateTimeField()
	enddate = pw.DateTimeField()
	

	
#database.drop_table(Videos)
#Videos.create_table()

#Songs.create_table()

tmdb.configure(tmdbAPI)

def LoadByTMDB(id):
	movie = tmdb.getMovieInfo(id)
	data={}

	data['type']=0
	data['title']=movie['name']
	data['date']=movie['released']
	data['rating']=int(float(movie['rating'])*10)
	data['runtime']=movie['runtime']
	data['tagline']=movie['tagline']
	data['summary']=movie['overview']
	data['budget']=movie['budget']
	data['revenue']=movie['revenue']
	now = datetime.datetime.now()
	data['cachedate']="%d-%d-%d" % (now.year, now.month, now.day)
	
	return data

def LoadByFilename(filename):
	print("Looking up:",filename)
	if(os.path.splitext(filename)[1] in MUSIC_FILES):
		if(Songs.select().where(filename=filename).count()==0):
			Songs(**LookupAcoustID(filename)).save()
	
	#results = tmdb.search(os.path.splitext(os.path.basename(filename))[0])
	#if(len(results)>0):
	#	searchResult = results[0]
	#	data = LoadByTMDB(searchResult['id'])
	#	data['filename']=filename
	#	
	#	row=Videos(**data)
	#	row.save()

def LookupAcoustID(path):
	result = {
		"filename": path,
		"title": os.path.basename(os.path.splitext(path)[0]),
		"artist": "Unknown",
	}
	for score, recording_id, title, artist in acoustid.match(AcoustidAPI, path):
		result['title']=title
		result['artist']=artist
		result['musicbrainz']=recording_id
	
	return result

def LookupMusicBrainz(fullpath):
	data = acoustid.match(AcoustidAPI, fullpath)
	if data['status'] != 'ok':
		return result
	if 'results' not in data:
		return result
	if(len(data['results'])==0):
		return result
	
	
	#trackId = data['results'][0]['recordings'][0]['id']
	q = ws.Query()
	# artist=False, releases=False, puids=False, artistRelations=False, releaseRelations=False, trackRelations=False, urlRelations=False, tags=False, ratings=False, isrcs=False
	include = ws.TrackIncludes(artist = True, tags=True, releases=True)
	
	track = q.getTrackById(trackId, include)
	
	result['title']=track.getTitle()
	result['artist']=track.getArtist()
	release = track.getReleases()
	
	result['album']=release[0].getTitle()
	

if __name__ == "__main__":
	import sys
	if(sys.argc > 0):
		if(sys.argv[1]=="run"):
			print("Starting scan")

			for root, dirs, files in os.walk('/var/media/music/'):
				for f in files:
					fullpath = os.path.join(root, f)
					LoadByFilename(fullpath)

