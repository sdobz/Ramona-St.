#!/usr/bin/env python
import library.web as web
import inspect

from plugin_manager import plugin_loaded

import os, sys


# A helper class that includes standard page type stuff
class page:
	def render(self,template,*args):
		if not(hasattr(self,"render_instance")):
			template_dir = os.path.join("ramonast","plugins",self.get_plugin(),"templates")
			self.render_instance = web.template.render(template_dir)
		render_func = getattr(self.render_instance,template)

		return unicode(render_func(*args))
		
	# This will figure out the plugin that the instance derives from
	def get_plugin(self):
		# The return is probably something like plugins.index.index
		return self.__module__.split(".")[1]
	
	def get_class(self):
		return self.__class__.__name__
		
	def head(self,*args):
		return self.render("head",*args)
	
	def body(self,*args):
		return self.render("body",*args)
	
	def html(self, head = [], body = []):
		return theme().encapsulate(self.head(*head),self.body(*body))


def theme():
	if(plugin_loaded("theme")):
		return sys.modules['plugins.theme'].theme()