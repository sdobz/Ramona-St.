#!/usr/bin/env python
# The main index page of the system

from page import page, static
from plugin_manager import depends_on
depends_on(["theme"])

urls = (
	"/", "index",
)

class index(page):
	def GET(self):
		return self.html()