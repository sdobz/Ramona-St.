#!/usr/bin/env python
# sdobz 7/30/11
import sys
sys.path.append("/var/apps/RamonaSt/ramonast")

import library.web as web
import plugin_manager, config

web.config.debug = True

urls = []
for plugin_name in config.plugins:
	plugin = plugin_manager.load(plugin_name)
	
	for url, handler in plugin_manager.get_urls(plugin_name):
		handler_name = plugin.__name__ + "." + handler
		
		urls.append(url)
		urls.append(handler_name)

app = web.application(urls, globals(), autoreload=False)

from static import StaticMiddleware
if __name__ == "__main__": app.run(StaticMiddleware)
