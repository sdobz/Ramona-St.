#!/usr/bin/env python

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import re, string, pickle
from applications import BaseApplication
from page import page

from plugin_manager import depends_on
depends_on(["theme"])

MINECRAFT_DIR = '/var/apps/minecraft'
STORAGE_DIR = '/var/apps/minecraft/script/RamonaSt'
WIKI_BASE = 'http://www.minecraftwiki.net'

urls = ( "/minecraft/(.*)", "minecraft" )

class minecraft(page):
	def GET(self,dir):
		if(dir != ""):
			application.givestr(dir)
		items = ""
		for item in pickle.load(open(STORAGE_DIR + '/cache.pickle','r')):
			items += self.render("item",Item.Load(item))
		return self.html([],[items])

class MinecraftApplication(BaseApplication):
	def givestr(self, dir):
		args = string.split(dir,"/")
		print(args)
		if(len(args)<3):
			return False
		# pattern = re.compile('[a-zA-Z 0-9]+')
		pattern = re.compile('\W+')
		name = pattern.sub('', args[0])
		quantity = int(args[1])
		item = int(args[2])
		self.give(name, quantity, item)
		
	def give(self, name, quantity, item):
		while(quantity > 0):
			args=["sudo","control","minecraft","give",name,str(item),str(quantity % 64)]
			self.control(args)
			quantity -= 64
			# give person item quant

application = MinecraftApplication(
	pretty_name = "Minecraft",
	name = "minecraft",
	description = "Minecraft manager frontend",
	image_url = "/static2/minecraft/minecraft.png",
)

class Item:
	def __init__(self):
		self.imageurl = ""
		self.imagehtml = ""
		self.dec = ""
		self.wikiurl = ""
		self.name = ""
	
	# Load and Save workaround a WSGI limitation
	@staticmethod
	def Load(d):
		o = Item()
		o.imageurl = d['imageurl']
		o.imagehtml = d['imagehtml']
		o.dec = d['dec']
		o.wikiurl = d['wikiurl']
		o.name = d['name']
		return o
		
	def Save(self):
		return {
			'imageurl': self.imageurl,
			'imagehtml': self.imagehtml,
			'dec': self.dec,
			'wikiurl': self.wikiurl,
			'name': self.name
		}
	
	def __str__(self):
		return "Minecraft item: " + self.name + " - " + str(self.dec)

def GetValues():
	soup = BeautifulSoup(open(STORAGE_DIR + '/cache.html','r'))
	items = []
	for tr in soup.find_all("tr"):
		if(tr.td and 'height' in tr.td.attrs):
			# For WHATEVER reason, the height of every itemid table is 27px
			if(tr.td['height'] == "27px"):
				#<tr>
				#<td height="27px"> <a href="/wiki/File:Stone.png" class="image"><img alt="Stone.png" src="/images/thumb/d/d4/Stone.png/25px-Stone.png" width="25" height="25" /></a> </td>
				#<td> 01 </td>
				#<td> 1 </td>
				#<td> <a href="/wiki/Stone" title="Stone">Stone</a>
				#</td></tr>
				td1, td2, td3, td4 = tr.find_all("td")
				curitem = Item()
				if(td1 and td1.a and td1.a.img):
					curitem.imageurl = WIKI_BASE + tr.td.a.img['src']
				if(td2):
					if(td2.span):
						curitem.dec = string.strip(td2.span.contents[0])
					else:
						curitem.dec = string.strip(td2.contents[0])
				
				if(td4):
					if(td4.a and td4.a.contents[0] != "D"):
						curitem.wikiurl = WIKI_BASE + td4.a['href']
					
					# Handle nasty partial href descriptions
					for item in td4.contents:
						if(type(item) == NavigableString):
							curitem.name += str(item)
						elif(item.name == "a" and item.contents[0] not in ["D","T","B","I"]):
							curitem.name += " " + string.strip(item.contents[0])
					
					curitem.name = string.strip(curitem.name)
					
				items.append(curitem.Save())
				
			if(tr.td['height'] == "23px"):
				# Is an "item" item.
				#<tr>
				#<td height="23px"> <div style="position: relative; height: 16px; width: 16px; overflow: hidden; display: inline-block; vertical-align: middle;"><div style="position: absolute; height: 256px; width: 256px; top: -80px; left: -32px;"><img alt="ItemCSS.png" src="/images/f/f5/ItemCSS.png" width="256" height="256" /></div></div> </td>
				#<td> 256 </td>
				#<td> 100 </td>
				#<td> <a href="/wiki/Iron_Ingot" title="Iron Ingot">Iron</a> <a href="/wiki/Shovel" title="Shovel">Shovel</a>
				#</td></tr>
				td1, td2, td3, td4 = tr.find_all("td")
				curitem = Item()
				if(td1):
					# This uses a nasty offset thing with a central image. Just store the html.
					td1.div.div.img['src'] = WIKI_BASE + td1.div.div.img['src']
					for item in td1.contents:
						curitem.imagehtml += str(item)
				if(td2):
					if(td2.span):
						curitem.dec = string.strip(td2.span.contents[0])
					else:
						curitem.dec = string.strip(td2.contents[0])
				
				if(td4):
					if(td4.a and td4.a.contents[0] != "D"):
						curitem.wikiurl = WIKI_BASE + td4.a['href']
					
					# Handle nasty partial href descriptions
					for item in td4.contents:
						if(type(item) == NavigableString):
							curitem.name += str(item)
						elif(item.name == "a" and item.contents[0] not in ["D","T","B","I"]):
							curitem.name += string.strip(item.contents[0])
					
					curitem.name = string.strip(curitem.name)
				
				items.append(curitem.Save())
	
	pickle.dump(items,open(STORAGE_DIR + '/cache.pickle','wb'))
			
	
def CachePage():
	import urllib
	FilePage = urllib.urlopen('http://www.minecraftwiki.net/wiki/Data_values')
	FileCache = open(STORAGE_DIR + '/cache.html','w')
	for lines in FilePage.readlines():
		FileCache.write(lines)

	FilePage.close()
	FileCache.close()


if __name__ == "__main__":
	CachePage()
	GetValues()