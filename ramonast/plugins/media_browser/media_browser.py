#!/usr/bin/env python

from page import page
from plugin_manager import depends_on
import database as db
import library.web as web
from peewee import Q
depends_on(["theme"])

urls = (
	"/media_browser/ajax/music/artist/songs_by/(.*)", "songs_by",
	"/media_browser/ajax/music/artist/(.*)", "artist",
	"/media_browser/ajax/music/", "music",
	"/media_browser/ajax/", "root",
	"/media_browser/(.*)", "index",
)

class index(page):
	def GET(self,path):
		if(path != ""):
			raise web.seeother("/media_browser/#/"+path)
		return self.render("index")
q
class root(page):
	def GET(self):
		return self.render("root")

class music(page):
	def GET(self):
		return self.render("music")


    
    if(start == "num"):
			return self.render("starts_with", db.Artist.select().where(
				Q(sortname__istartswith = '0') |
				Q(sortname__istartswith = '1') |
				Q(sortname__istartswith = '2') |
				Q(sortname__istartswith = '3') |
				Q(sortname__istartswith = '4') |
				Q(sortname__istartswith = '5') |
				Q(sortname__istartswith = '6') |
				Q(sortname__istartswith = '7') |
				Q(sortname__istartswith = '8') |
				Q(sortname__istartswith = '9')))
		if(start.isalpha()):
			return self.render("starts_with", db.Artist.select().where(sortname__istartswith = start))
	
	def get_specific(self,artist_id):
		for artist in db.Artist.select().where(id = artist_id):
			return self.render("artist", artist)
		raise web.notfound()

