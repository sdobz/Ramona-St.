#!/usr/bin/python

import os
import applications
from library.web.utils import group

PLUGIN_DIR = "plugins."

plugins = {}

def load(name):
	if(plugin_loaded(name)):
		raise PluginAlreadyLoaded

	#try:
	plugins[name] =  __import__(PLUGIN_DIR + name, globals(), locals(), [name], -1)
	#except ImportError:
		# Also hit by legitimate import errors in plugins
	#	raise PluginNotFound(name)
		
	plugin = plugins[name]

	if(hasattr(plugin,"application")):
		applications.applications.append(plugin.application)
	if(hasattr(plugin,"applications")):
		for app in plugin.applications:
			applications.applications.append(app)
	
	return plugin

# Format the url from a list to a bunch of tuples
def get_urls(name):
	if not(plugin_loaded(name)):
		raise PluginNotLoaded
	
	if not(hasattr(plugins[name],"urls")):
		return []
	
	return list(group(plugins[name].urls, 2))

def depends_on(deps):
	for dep in deps:
		if not(plugin_loaded(dep)):
			raise MissingDependancy(dep)

def plugin_loaded(plugin):
	return (plugin in plugins)

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