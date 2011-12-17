#!/usr/bin/env python
import web

# Needs updating to new RamonaSt module format

render = web.template.render('templates/chart')

class chart(object):
	def __init__(self,id):
		self.properties = {
			'id':			'',
			'cssclass':		'chart',
			'width':		200,
			'height':		200,
			'charthtml':	'',
			'chartcss':		'',
			'usercss':		'',
		}
		self.properties['id'] = id
	def setsize(self,width,height):
		self.properties['width']  = width
		self.properties['height'] = height
		
	def html(self):
		self.properties['charthtml'] = self.charthtml()
		return str(render.chart(self.properties))
	def css(self):
		self.properties['chartcss'] = self.chartcss()
		return str(render.chartcss(self.properties))
	
	def charthtml(self):
		return ''
	def chartcss(self):
		return ''

class pie(chart):
	slices=[]
	zero=0
	def __init__(self,id):
		super(self.__class__,self).__init__(id)
		self.cssclass='chart pie'
	def clear(self):
		self.slices=[]
	def setzero(self,zero):
		self.zero=zero
		
	def addslice(self,item,start,end,color):
		# This forces it to xxx.xx
		start=float(int(start*100))/100
		end=float(int(end*100))/100
		self.slices.append({
			'item':		item,
			'start':	-start,
			'end':		-end,
			'color':	color 
		})
	
	def charthtml(self):
		html=''
		for slice in self.slices:
			html += str(render.pieslice(self.properties,slice))
		return html
	
	def chartcss(self):
		css=str(render.piecss(self.properties))
		for slice in self.slices:
			slice['start']-=self.zero
			slice['end']  -=self.zero
			css += str(render.pieslicecss(self.properties,slice))
		return css
