#!/usr/bin/env python
import library.web as web
import inspect

import os


# A helper class that includes standard page type stuff
class page:
	def render(self,template,*args):
		if not(hasattr(self,"render_instance")):
			template_dir = os.path.join("ramonast","plugins",self.get_plugin(),"templates")
			self.render_instance = web.template.render(template_dir)

		render_func = getattr(self.render_instance,template)

		return render_func(*args)
		
	# This will figure out the plugin that the instance derives from
	def get_plugin(self):
		# The return is probably something like plugins.index.index
		return self.__module__.split(".")[1]
	
	def get_class(self):
		return self.__class__.__name__
	
	def html(self):
		return self.render(self.get_class(),"head","body")

		
# If you extend static it can be used to serve the static files for a plugin

# Ex:
# import page
# urls = ( "/minecraft/static/(.*)", "static" )
# class static(page.static):
#
class static:
	def GET(self, url):
		return "ok"