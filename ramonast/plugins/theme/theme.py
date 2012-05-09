#!/usr/bin/env python
# Controls the theme of the pages

from page import page
import config

# This is used to gain access to the theme templates
class theme(page):
	def encapsulate(self, head, body):
		return self.render(config.theme,head,body)
		
class ThemeNotFound(Exception):
	""" The requested theme in the config is not found """