from library.web.template import render as make_renderer
render = make_renderer('templates/browse')
from index import render as index_render
import os

mediaroot="/var/media"

class browse:
	def GET(self,dir):
		webpath=dir
		dir=os.path.normpath(os.path.join(mediaroot,dir))

		if(dir[:len(mediaroot)]!=mediaroot):
			raise web.notfound("You cannot go up directories.")
			
		if not(os.path.isdir(dir)):
			head='<script type="text/javascript" src="/static/jwplayer/jwplayer.js"></script>'
			return index_render.index(head,render.player('/stream/'+webpath))
		body=''
		dirs=['..']
		files=[]
		for file in os.listdir(dir):
			fullname=dir+file
			if(os.path.isdir(fullname)):
				dirs.append(file)
			else:
				files.append(file)
		dirs.sort()
		files.sort()
		
		for dir in dirs:
			body+='<a href="/browse/%s/%s">%s</a><br>\n' % (webpath,dir,dir)
		body+='<hr>\n'
		for file in files:
			body+='<a href="/stream/%s/%s">%s</a><br>\n' % (webpath,file,file)
			
		return index_render.index('',body)