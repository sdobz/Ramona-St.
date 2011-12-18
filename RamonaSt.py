#!/usr/bin/env python
# sdobz 7/30/11
import ramonast.library.web as web

# Ramona Dr. modules
from ramonast.stream import stream
from ramonast.index import index
from ramonast.appcontrol import appcontrol

web.config.debug = True

urls = (
  '/', 'index',
  '/stream/(.*)', 'stream',
  '/appcontrol/(.*)', 'appcontrol',
)

app = web.application(urls, globals(),  autoreload=False)
		
if __name__ == "__main__": app.run()
