#!/usr/bin/env python

from library import web
import os, os.path, datetime
from library.tmdb import tmdb
from library.tvdb import tvdb_api as tvdb
import peewee as pw

import library.pyacoustid.acoustid as acoustid
import musicbrainz2.webservice as ws
# import pylast

from mutagen import File as GetTags

from config import *

# Various errors:
from struct import error as StructError
from mutagen.mp3 import HeaderNotFoundError
from mutagen.mp4 import MP4StreamInfoError

from warnings import warn


MUSIC_FILES=['.mp3','.m4a','.m4p','.mp4','.wav']
VIDEO_FILES=[]
REQUEST_INTERVAL = 0.33 # 3 requests/second.
MAX_CACHE_AGE = 360

database = pw.MySQLDatabase(MySQLDatabase, user=MySQLUser, passwd=MySQLPassword)
database.connect()

tmdb.configure(tmdbAPI)

#lastfm = pylast.LastFMNetwork(api_key = LastFMAPI, api_secret = LastFMSecret, username = "sdobz", password_hash = "10ca7331ff13868563a7773634558580")
#lastfm.enable_caching()

class LookupError(Exception):
	""" There was an error loading a thing. """
	def __init__(self,msg,file = "Unknown"):
		self.msg = msg
		self.file = file
	def __str__(self):
		return self.file + ": " + self.msg
		
class BaseModel(pw.Model):
	class Meta:
			database = database

class Videos(BaseModel):
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
	
class Fingerprints(BaseModel):
	fingerprint = pw.TextField()
	duration = pw.IntegerField()
	submitted = pw.DateTimeField()
	
	def NeedsRefresh(self):
		return (self.submitted == None or (datetime.datetime.now() - self.submitted).days > MAX_CACHE_AGE)
	
	def Lookup(self,song):
		now = datetime.datetime.now()
		self.submitted = "%d-%d-%d" % (now.year, now.month, now.day)
	
		try:
			response=acoustid.parse_lookup_result(acoustid.lookup(AcoustidAPI, self.fingerprint, self.duration))
		except acoustid.WebServiceError:
			raise LookupError("Error submitting acoustid fingerprint")
		else:
			for score, recording_id, title, artist in response:
				song.title = title
				song.artist = artist
				song.trackid = recording_id
	
class Songs(BaseModel):
	filename = pw.CharField(unique=True)
	title = pw.CharField()
	artist = pw.CharField()
	trackid = pw.CharField(size=36)
	fingerprint = pw.ForeignKeyField(Fingerprints)
	
	@staticmethod
	def GetFromFile(path):
		try:
			song = Songs.get(filename = path)
		except Songs.DoesNotExist:
			song = Songs(
				filename = path,
				submitted = "0-0-0"
			)
			song.LoadMetaFromFile()
		
		return song
	
	def LoadMetaFromFile(self):
		filename = self.filename
		if(os.path.exists(filename)==False):
			raise LoadError("File does not exist",filename)
			
		try:
			tags = GetTags(filename, easy = True)
		except (UnicodeDecodeError,StructError,HeaderNotFoundError,MP4StreamInfoError):
			warn("Error decoding file to read tags: "+filename)
			self.title = os.path.splitext(os.path.basename(filename))[0]
		else:
			if(tags):
				if("title" in tags):
					self.title = tags['title'][0]
				else:
					self.title = os.path.splitext(os.path.basename(filename))[0]
				if("artist" in tags):
					self.artist = tags['artist'][0]
		
	def GetFingerprint(self):
		try:
			return self.fingerprint
		except Fingerprints.DoesNotExist:
			try:
				duration,fp = acoustid.fingerprint_file_fpcalc(self.filename)
			except acoustid.FingerprintGenerationError:
				raise LookupError("Error generating fingerprint",self.filename)
			
			return Fingerprints(
				fingerprint = fp,
				duration = duration,
			)
	
	@staticmethod
	def Import(path):
		print(path)
		song = Songs.GetFromFile(path)
		
		if(song.id > 34298):
			return
		
		print("    Loading")
		fingerprint = song.GetFingerprint()
		
		if(fingerprint.NeedsRefresh()):
			fingerprint.Lookup(song)

		fingerprint.save()
		song.fingerprint = fingerprint
		song.save()
		if(song.title):
			print("    "+song.title)
	
	def Move(self,newpath):
		
	
		
class Artists(BaseModel):
	artistid = pw.CharField(size=36,unique=True)
	name = pw.CharField()
	sortname = pw.CharField()
	disambiguation = pw.CharField()
	
class Tracks(BaseModel):
	trackid = pw.CharField(size=36,unique=True)
	title = pw.CharField()
	artist = pw.ForeignKeyField(Artists)

class Tags(BaseModel):
	item = pw.CharField(size=36)
	tag = pw.CharField()
	count = pw.IntegerField(size=2)
	
class Releases(BaseModel):
	releaseid = pw.CharField(db_index=True, size=36)
	title = pw.CharField()
	artist = pw.ForeignKeyField(Artists)

class ReleaseTracks(BaseModel):
	track = pw.ForeignKeyField(Tracks)
	release = pw.ForeignKeyField(Releases)
	tracknumber = pw.IntegerField(size=2)
	

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
	ext = os.path.splitext(filename)[1]
	if(ext in MUSIC_FILES):
		Songs.Import(filename)
	
	if(ext in VIDEO_FILES):
		results = tmdb.search(os.path.splitext(os.path.basename(filename))[0])
		if(len(results)>0):
			searchResult = results[0]
			data = LoadByTMDB(searchResult['id'])
			data['filename']=filename
			
			row=Videos(**data)
			row.save()
			
	
def D(first,second):
	if(first==None):
		return second
	return first
	
def LookupMusicBrainz(trackId):
	q = ws.Query()
	# artist=False, releases=False, puids=False, artistRelations=False, releaseRelations=False, trackRelations=False, urlRelations=False, tags=False, ratings=False, isrcs=False
	trackinclude = ws.TrackIncludes(artist = True, releases = True, tags = True)
	
	# artist=False, counts=False, releaseEvents=False, discs=False, tracks=False, artistRelations=False, releaseRelations=False, trackRelations=False, urlRelations=False, labels=False, tags=False, ratings=False, isrcs=False, releaseGroup=False
	releaseinclude = ws.ReleaseIncludes(tracks = True)
	
	try:
		trackrow = Tracks.get(trackid = trackId)
		return
	except Tracks.DoesNotExist:
		try:
			track = q.getTrackById(trackId, trackinclude)
		except ws.ResourceNotFoundError:
			return
	
		artist = track.getArtist()
	
		trackrow=Tracks(**{
			'trackid': trackId,
			'title': track.getTitle(),
		})
	
	if(artist):
		artistid = artist.getId()[-36:]
		try:
			artistrow = Artists().get(artistid = artistid)
		except Artists.DoesNotExist:
			artistrow = Artists(
				artistid = artistid,
				name = D(artist.getName(),"Unknown"),
				sortname = D(artist.getSortName(),""),
				disambiguation = D(artist.getDisambiguation(),""),
			)
	
	for tag in track.getTags():
		tagname = tag.getValue()
		count = tag.getCount()
		try:
			tagrow = Tags.get(item = trackrow.trackid, tag = tagname)
		except Tags.DoesNotExist:
			tagrow = Tags(
				item = trackrow.trackid,
				tag = tagname,
			)
		
		tagrow.count = count
		tagrow.save()
	
	releaserow = False
	releasetrackrow = False
	
	if(ReleaseTracks.select().where(track = trackrow).count()==0):
		print("    Getting first release...")
		for release in track.getReleases():
			releaserow = Releases(
				releaseid = release.getId()[-36:],
				title = release.getTitle(),
			)
			
			i=1
				
			release2 = q.getReleaseById(release.getId(), releaseinclude)
			for releasetrack in release2.getTracks():
				if(releasetrack.getId()[-36:] == trackId):
					releasetrackrow = ReleaseTracks(
						tracknumber = i,
					)
					
					break
				i+=1
			
			
			# Only do first release
			break
	else:
		print("    Release already loaded.")
	
	
	# In order to be atomic do the db saving at the end	
	artistrow.save()
	trackrow.artist = artistrow
	trackrow.save()
	
	if(releaserow):
		releaserow.artist = artistrow
		releaserow.save()
	if(releasetrackrow):
		releasetrackrow.releaseid = releaserow
		releasetrackrow.trackid = trackrow
		releasetrackrow.save()

	print("    Done")

def FindIssues():
	for song in Songs.select():
		if not(os.path.exists(song.filename)):
			print("Song does not have file: "+song.filename)
		

if __name__ == "__main__":
	import sys
	if(len(sys.argv) > 1):
		if(sys.argv[1]=="run"):
			print("Starting scan")

			for root, dirs, files in os.walk('/var/media/music/'):
				for f in files:
					fullpath = os.path.join(root, f)
					try:
						LoadByFilename(fullpath)
					except LookupError as err:
						print(err)
					
		if(sys.argv[1]=="clear"):
			for song in Songs.select():
				if not(os.path.exists(song.filename)):
					song.delete_instance()
		
		if(sys.argv[1]=="mb"):
			for song in Songs.select().where(trackid__ne = ""):
				try:
					LookupMusicBrainz(song.trackid)
				except ws.ConnectionError:
					pass
		
		if(sys.argv[1]=="issues"):
			FindIssues()
		
		if(sys.argv[1]=="fromtag"):
			num = str(Songs.select().where(trackid = "").count())
			i = 0
			for song in Songs.select().where(trackid = ""):
				if(song.trackid != ""):
					print(song.trackid)
				else:
					filename = song.filename
					try:
						tags = GetTags(filename, easy = True)
					except UnicodeDecodeError:
						print("Song decode error: "+filename)
					except struct.error:
						print("Song decode error: "+filename)
					except mutagen.mp3.HeaderNotFoundError:
						print("Song decode error: "+filename)
					
					song.title = tags['title'][0]
					song.artist = tags['artist'][0]
					song.save()
					
					i+=1
					
					print(str(i)+"/"+num)

