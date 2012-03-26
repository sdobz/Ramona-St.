#!/usr/bin/python

# List the acceptable applications
import library.rs_process as rs_process
applications=[]

CONTROL_COMMAND = ["sudo","control"]

class CommandAlreadyRunning(Exception):
	""" The command is already running """
	
class CommandNotRunning(Exception):
	""" The command is not running """

class BaseApplication:
	def __init__(self,**settings):
		# pretty_name
		# name
		# description
		# url
		# image_url
		# startfunc
		# stopfunc
		# restartfunc
		# statusfunc
		self.settings = settings
		self.commands = {}
		
	def get_pretty_name(self):
		if("pretty_name" in self.settings):
			return self.settings["pretty_name"]
		if("name" in self.settings):
			return self.settings["name"]
		return "Unknown"
	
	def get_name(self):
		if("name" in self.settings):
			return self.settings["name"]
		return "Unknown"
	
	def get_description(self):
		if("description" in self.settings):
			return self.settings["description"]
		return "Unknown"
	
	def get_url(self):
		if("url" in self.settings):
			return self.settings["url"]
		return "/"
	
	def get_image_url(self):
		if("image_url" in self.settings):
			return self.settings["image_url"]
		return "/content/index/apps/" & self.get_name() & ".png"
	
	def start(self):
		if("startfunc" in self.settings):
			return self.settings["startfunc"]()
		
		self.control(["start"])
	
	def stop(self):
		if("stopfunc" in self.settings):
			self.settings["startfunc"]()
		
		self.control(["stop"])
	
	def restart(self):
		if("restartfunc" in self.settings):
			return self.settings["restartfunc"]()
			
		self.control(["restart"])
	
	def status(self):
		if("statusfunc" in self.settings):
			return self.settings["statusfunc"]()
		
		return ("RUNNING" in self.control(["status"],block=True))
	
	def control(self,args,block=False):
		if(args[0] in self.commands):
			raise CommandAlreadyRunning(name)
		if(block):
			return rs_process.command(args)
		else:
			self.commands[args[0]] = rs_process.process(CONTROL_COMMAND+[self.get_name()]+args,60,True)
		
	def read(self,command):
		if(command in self.commands):
			out = self.commands[command].read()
			if out:
				return out
			else:
				del self.commands[command]
				return False
		else:
			raise CommandNotRunning

