#!/usr/bin/env python
# sdobz 7/30/11
import sys
sys.path.append("/var/apps/RamonaSt/ramonast")

import library.web as web

web.config.debug = True

#urls = (
#  '/',					'index',
#  '/stream/(.*)',		'stream',
#  '/appcontrol/(.*)',	'appcontrol',
#  '/browse/(.*)',		'browse',
#  '/minecraft/(.*)',	'minecraft'
#)

urls = []

import plugin_manager, config
for plugin_name in config.plugins:
	plugin = plugin_manager.load(plugin_name)
	
	for url, handler in plugin_manager.get_urls(plugin_name):
		handler_name = plugin.__name__ + "." + handler
		
		urls.append(url)
		urls.append(handler_name)

app = web.application(urls, globals(),  autoreload=False)
		
if __name__ == "__main__": app.run()
