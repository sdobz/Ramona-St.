#!/usr/bin/env python
# Controls the theme of the 

from page import page, static

class index(page):
	def GET(self):
		return self.html()