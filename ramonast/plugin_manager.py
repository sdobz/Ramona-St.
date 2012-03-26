#!/usr/bin/python

import os
import applications

PLUGIN_DIR = "plugins."

plugins = {}

def load(name):
	if(name in plugins):
		raise PluginAlreadyLoaded
	
	try:
		plugins[name] =  __import__(PLUGIN_DIR + name, globals(), locals(), [name], -1)
	except ImportError:
		raise PluginNotFound(name)
		
	plugin = plugins[name]
	
	if(hasattr(plugin,"application")):
		applications.applications.append(plugin.application)
	if(hasattr(plugin,"applications")):
		for app in plugin.applications:
			applications.applications.append(app)
	
	return plugin

# Format the url from a list to a bunch of tuples
def get_urls(name):
	if not(name in plugins):
		raise PluginNotLoaded
	
	if not(hasattr(plugins[name],"urls")):
		return []
	
	urls = []
	
	url = False
	handler = False
	
	for urlbit in plugins[name].urls:
		if(url != False):
			handler = urlbit
			
			urls.append((url,handler))
			url = False
		
		else:
			url = urlbit
	return urls

def depends_on(deps):
	for dep in deps:
		if not(dep in plugins):
			raise MissingDependancy(dep)

class PluginAlreadyLoaded(Exception):
	""" Plugin already loaded exception """

class PluginNotLoaded(Exception):
	""" Plugin not loaded """

class MissingDependancy(Exception):
	""" A plugin this plugin depends on isn't loaded yet """
	
# TODO: get this to print which plugin wasn't found
class PluginNotFound(Exception):
	""" Plugin already loaded exception """
	def __str__(self):
		return "Plugin not found: " + self.args