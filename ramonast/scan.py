#!/usr/bin/env python

# TVDB API E4A9298AF1FA826C
# TMDB API a95e77702c63a163c97b9d4414af09da

from library import web
import os, os.path, datetime
from library.themoviedb import tmdb
from library.tvdb import tvdb_api as tvdb
from pydo import *

initAlias('media_browser','mysql',('localhost','media_browser','HbUjzsaxjrysBn7x','media_browser'))
# db = web.database(dbn='mysql', db='media_browser', user='media_browser', pw='HbUjzsaxjrysBn7x')

tmdb.configure("a95e77702c63a163c97b9d4414af09da")

class VideoStore(PyDO):
	connectionAlias='media_browser'
	table='VIDEOS'
	fields = (
		('id',	'int(10)'),
		('filename',	'varchar(255)'),
		('type',		'enum(\'SHOW\',\'MOVIE\',\'OTHER\')'),
		('title',		'varchar(255)'),
		('date',		'date'),
		('rating',		'smallint(6)'),
		('runtime',		'smallint(6)'),
		('tagline',		'varchar(400)'),
		('summary',		'text'),
		('budget',		'int(11)'),
		('revenue',		'int(11)'),
		('cachedate',	'date')
	)
	unique = [ 'id', 'filename' ]

def LoadByTMDB(id):
	movie = tmdb.getMovieInfo(id)
	data={}
	Store=VideoStore(id=id)
	data['type']='MOVIE'
	data['title']=movie['name']
	print(data['title'])
	data['date']=movie['released']
	data['rating']=int(float(movie['rating'])*10)
	data['runtime']=movie['runtime']
	data['tagline']=movie['tagline']
	data['summary']=movie['overview']
	data['budget']=movie['budget']
	data['revenue']=movie['revenue']
	now = datetime.datetime.now()
	data['cachedate']="%d-%d-%d" % (now.month, now.day, now.year)
	Store.updateValues(data)
	Store.commit()
	return Store

def LoadByFilename(filename):
	results = tmdb.search(os.path.splitext(os.path.basename(filename))[0])
	if(len(results)>0):
		searchResult = results[0]
		Store = LoadByTMDB(searchResult['id'])
		Store['filename']=filename
		Store.commit()
			

print("Starting scan")

i = 0
for root, dirs, files in os.walk('/var/media/videos/Movies'):
	for f in files:
		if(i>5):
			break
		fullpath = os.path.join(root, f)
		LoadByFilename(fullpath)