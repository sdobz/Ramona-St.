#!/usr/bin/env python

if(__name__ == "__main__"):
	import sys
	sys.path.append("/var/apps/RamonaSt/ramonast")

from page import page
import database as db
import library.web as web
# import library.peewee as pw
import library.rs_pwv as pw

urls = (
	"/media_browser/ajax/music/artist/(.*)", "artist",
	"/media_browser/ajax/music/album/(.*)", "release",
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
	
class filter_list(page):
	def GET(self, arg_str):
		return self.render("list_iter", self.make_list(arg_str))
	
	def make_list(self, arg_str):
		args = arg_str.split("+")

		query = self.get_query()
		
		# Parse args builds up the query based off of the arguments
		query = self.parse_args(query, args)
		
		return query.iterators()

	def parse_args(self, query, args):
		# The args are a broken up list in the form:
		# [ "field__field_arg=value", ... ]
		while(len(args) > 0):
			# These two bits break up the argument
			q = args[0].split("=",1)
			if(len(q)>1):
				field, value = q
			else:
				field = q[0]
				value = ""
			
			q = field.split("__",1)
			if(len(q)>1):
				field, field_arg = q
			else:
				field = q[0]
				field_arg = ""
				
			# This is in the form "paginate=pagenum,itemsperpage"
			if(field == "paginate"):
				page, items = value.split(",")
				query = query.paginate(int(page), int(items))
			
			if(self.view.has_field(field)):
				# If it is a matchable field
				
				if(field_arg == "asc" or field_arg == "desc"):
					query = query.order_by((field, field_arg))
			
				if(field_arg == "" or field_arg == "is"):
					query = query.where(**{field: value})
				if(field_arg == "startswith"):
					query = self.starts_with(query, field, value)
				if(field_arg == "regexp"):
					query = self.regexp(query, field, value)
				
			args = args[1:]
		return query
		
	def starts_with(self, query, field, arg):
		if(arg == "?"):
			return self.regexp(query, field, "^[^0-9A-Za-z]'")
		if(arg == "num"):
			return self.regexp(query, field, "^[0-9]")
			
		return query.where(**{field + "__istartswith": arg})
		
	def regexp(self, query, field, reg):
		return query.filter(pw.R("%s REGEXP %s", field, reg))
	
	def get_query(self):
		return self.view.select_view()

# The view sugar allows an optimized iteration of the list
class artist(filter_list):
	class artist_view(db.View,db.Artist):pass
	view = artist_view("id","name")
	
# Release results in a bunch of albums with their artists
class release(filter_list):
	display = ["albumid", "album", "artistid"]
	fields = {
		"album_id": {
			"field_name": "id"
		},
		"album": {
			"field_name": "title"
		},
		"artistid": {
			"field_name": "id",
			"model": db.Artist,
		},
		"artist": {
			"field_name": "name",
			"model": db.Artist,
		},
	}
	model = db.Release
	joins = staticmethod(lambda q: q.join(db.Artist))

class track(filter_list):
	display = ["trackid", "track", "artistid", "artist", "albumid", "album"]
	fields = {
		"trackid": {
			"field_name": "id"
		},
		"track": {
			"field_name": "title"
		},
		"artist": {
			"field_name": "name",
			"model": db.Artist,
			"get": lambda row: row.artist
		},
		"artistid": {
			"field_name": "id",
			"model": db.Artist,
		},
		"album": {
			"field_name": "title",
			"model": db.Release,
		},
		"albumid": {
			"field_name": "id",
			"model": db.Release,
		},
	}
	model = db.Track
	joins = staticmethod(lambda q: q.join(db.Artist).switch(db.Track).join(db.ReleaseTrack).join(db.Release))

if(__name__ == "__main__"):
	import timeit

	#o = artist()
	
	o = artist()
	print(o.view.select_view().sql())

	#render = web.template.frender('/var/apps/RamonaSt/ramonast/plugins/media_browser/templates/list_iter.json')
	#query = ""
	#stmt = "print(len(str(render(o.make_list(\"%s\")))))" % query

	#num = 1
	
	#setup = "from __main__ import render, o"
	# setup += ";gc.enable()"
	
	#print("#1 %s iterations: %s" % (num,timeit.Timer(stmt, setup).timeit(num)))