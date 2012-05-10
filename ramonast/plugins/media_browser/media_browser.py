#!/usr/bin/env python

from page import page
from plugin_manager import depends_on
import database as db
import library.web as web
from peewee import R
from re import escape as escape

depends_on(["theme"])

urls = (
	#"/media_browser/ajax/music/artist/songs_by/(.*)", "songs_by",
	"/media_browser/ajax/music/artist/(.*)", "artist",
	"/media_browser/ajax/music/song/(.*)", "track",
	"/media_browser/ajax/music/", "music",
	"/media_browser/ajax/", "root",
	"/media_browser/(.*)", "index",
)

class index(page):
	def GET(self,path):
		if(path != ""):
			raise web.seeother("/media_browser/#/"+path)
		return self.render("index")
		
class root(page):
	def GET(self):
		return self.render("root")

class music(page):
	def GET(self):
		return self.render("music")

class abc_list(page):
	def make_list(self, arg_str):
		if(arg_str == ""):
			return self.render("abc_list")

		args = arg_str.split("+")

		query = self.get_query()
		
		# Parse args builds up the query based off of the arguments
		query = self.parse_args(query, args)
		
		query = query.execute()
		
		# Build rows is a generator takes a database result and formats it into 
		# something ready to be shoved into the template
		query_iter = self.build_rows(query.iterator())
		
		return query_iter


	def parse_args(self, query, args):
		while(len(args) > 0):
			q = args[0].split("=",1)
			if(len(q)>1):
				key, value = q
			else:
				key = q[0]
				value = ""
			
			q = key.split("__",1)
			if(len(q)>1):
				key, key_arg = q
			else:
				key = q[0]
				key_arg = ""
			
			if(key == "paginate"):
				page, items = value.split(",")
				query = query.paginate(page, items)
			
			if(key in self.select_columns):
				if(key_arg == "asc"):
					query = query.order_by((key, "asc"))
				if(key_arg == "desc"):
					query = query.order_by((key, "desc"))
			
				if(key_arg == "" or key_arg == "is"):
					# This unwraps key value into the form .where(key = value)
					query = query.where(**{key: value})
				if(key_arg == "startswith"):
					query = self.starts_with(query, key, value)
				if(key_arg == "regexp"):
					query = self.regexp(query, key, value)
				
			args = args[1:]
		return query

	def build_rows(self,query_iter):
		# These items are shoved into a ','.join() later
		for result in query_iter:
			# This is an iterator that looks each column up in the result and returns the value
			yield (getattr(result,column) for column in self.display_columns)

	def starts_with(self, query, field, arg):
		if(arg == "?"):
			return self.regexp(query, field, "^[^0-9A-Za-z]'")
		if(arg == "num"):
			return self.regexp(query, field, "^[0-9]")
			
		return query.where(**{field + "__istartswith": arg})
		
	def regexp(self, query, field, reg):
		return query.filter(R("%s REGEXP %s", field, reg))

class artist(abc_list):
	def __init__(self):
		self.display_columns = ["name"]
		self.select_columns = ["id","name","sortname"]
	def get_query(self):
		return db.Artist.select()

class track(abc_list):
	def __init__(self):
		self.display_columns = ["title"]
		print(self.get_query().sql())
	
	def GET(self,inp):
		return ""
	
	def get_query(self):
		return db.Track.select().join(db.Artist)

def mark_last(items): 
	items = iter(items) 
	last = items.next()
	for item in items: 
		yield False, last 
		last = item
	yield True, last
