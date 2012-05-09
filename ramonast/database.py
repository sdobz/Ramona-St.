#!/usr/bin/env python

# Utilities extend the classes listed here for interaction.
# For example, scan.py will implement a load by filename method.

import peewee as pw
from config import *

database = pw.MySQLDatabase(MySQLDatabase, user=MySQLUser, passwd=MySQLPassword)
database.connect()

class BaseModel(pw.Model):
	class Meta:
		database = database

class Movie(BaseModel):
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

class Show(BaseModel):
	name = pw.CharField()
	tvdbid = pw.IntegerField()
	genre = pw.CharField()
	overview = pw.TextField()
	rating = pw.IntegerField()
	actors = pw.CharField()
	
class Episode(BaseModel):
	name = pw.CharField()
	show = pw.ForeignKeyField(Show)
	tvdbid = pw.IntegerField()
	airdate = pw.DateTimeField()
	gueststars = pw.CharField()
	overview = pw.TextField()
	rating = pw.IntegerField()

class Fingerprint(BaseModel):
	fingerprint = pw.TextField()
	duration = pw.IntegerField()
	submitted = pw.DateTimeField()

class Song(BaseModel):
	filename = pw.CharField(unique=True)
	title = pw.CharField()
	artist = pw.CharField()
	trackid = pw.CharField(size=36)
	fingerprint = pw.ForeignKeyField(Fingerprint)

class Artist(BaseModel):
	artistid = pw.CharField(size=36,unique=True)
	name = pw.CharField()
	sortname = pw.CharField()
	disambiguation = pw.CharField()
	
class Track(BaseModel):
	trackid = pw.CharField(size=36,unique=True)
	title = pw.CharField()
	artist = pw.ForeignKeyField(Artist)

class Tag(BaseModel):
	item = pw.CharField(size=36)
	tag = pw.CharField()
	count = pw.IntegerField(size=2)
	
class Release(BaseModel):
	releaseid = pw.CharField(db_index=True, size=36)
	title = pw.CharField()
	artist = pw.ForeignKeyField(Artist)

class ReleaseTrack(BaseModel):
	track = pw.ForeignKeyField(Track)
	release = pw.ForeignKeyField(Release)
	tracknumber = pw.IntegerField(size=2)