#!/usr/bin/python

# Serving static files
import library.web as web
from web.httpserver import StaticApp
from plugin_manager import plugin_loaded
import posixpath, os, urllib

# TODO: make more configurable

class StaticMiddleware:
	"""WSGI middleware for serving static files, with additional plugin functionality """
	# http://stackoverflow.com/questions/6960295/changing-the-static-directory-path-in-webpy
	def __init__(self, app, prefix='/static2/', root_path='static/'):
		self.app = app
		self.prefix = prefix
		self.root_path = root_path

	def __call__(self, environ, start_response):
		path = environ.get('PATH_INFO', '')
		path = self.normpath(path)

		if path.startswith(self.prefix):
			path = web.lstrips(path, self.prefix)
			plugin = path.split(os.sep)[0]
			
			if(plugin_loaded(plugin)):
				newpath = path.split(os.sep)[1:]
				environ["PATH_INFO"] = os.path.join('ramonast', 'plugins', plugin, 'static', *newpath)
			else:
				environ["PATH_INFO"] = os.path.join(self.root_path, path)
				
			return StaticApp(environ, start_response)
		else:
			return self.app(environ, start_response)

	def normpath(self, path):
		path2 = posixpath.normpath(urllib.unquote(path))
		if path.endswith("/"):
			path2 += "/"
		return path2