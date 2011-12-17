#!/usr/bin/env python
# sdobz 7/30/11
import ramonast.library.web as web

# Ramona Dr. modules
import ramonast.helpers
from ramonast.stream import stream

render = web.template.render('static/templates/',globals={
	'helpers'	:ramonast.helpers,
})
web.config.debug = True
 
urls = (
  '/', 'index',
  '/apps/(.*)', 'apps',
  '/rcmd/(.*)', 'rcmd',
  '/stream/(.*)', 'stream',
)

app = web.application(urls, globals(),  autoreload=False)

class index:
    def GET(self):
		return render.index()

class apps:
	def GET(self,action):
		return helpers.handleapps(action) or render.applications()

class rcmd:
	def GET(self,token):
		return helpers.handlercmd(token)
		
if __name__ == "__main__": app.run()
