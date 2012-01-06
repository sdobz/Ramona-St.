#!/usr/bin/python

# As of 12/17/11 this module does NOT work, and doesn't conform to RamonaSt
# module format. Will be updated later --sdobz

import os, subprocess, time
from random import random

commands={}
port = 7979
command_dir="/var/apps/control/init.d"

actions = [
	'start',
	'stop',
	'restart',
	'status'
]

def action(app,action,block=False):
	log("=== NEW ACTION")
	if not(os.path.exists(os.path.join(command_dir,action))):
		return "Invalid app"
	if not (action in actions):
		return "Invalid action"
	
	if(block):
		return runcmd(["sudo","control",app,action])
	else:
		log("Responding...")
		prg = 
def rcmd(app,action):
	if not (app in apps):
		return "Invalid app"
	if not (action in actions):
		return "Invalid action"
	
	pid = daemon()
	if not(pid):
		return "Command not running"
	
	return xmlrpcclient().rcmd(app,action)
	
def runcmd(args):
	# Run the args and return the output
	return subprocess.check_output(args)

def getresponse(pid,func,app,action):
	# Write to the stdin of the daemon
	with open("/proc/"+pid+"/fd/0","w") as f:
		f.write(func+" "+app+" "+action)
	
	# Read the ensuing output
	with open("/proc/"+pid+"/fd/1","r") as f:
		return f.read()
	
def running(app):
	if("RUNNING" in action(app,"status",block=True)):
		return True
	return False

def startup(app):
	if("YES" in action(app,"checkstartup",block=True)):
		return True
	return False

def log(text):
	print(text)

class command:
	def __init__(self,app,action):
		global commands
		if app+action in commands:
			return False
		
		self.proc=self.makeprocess(app,action)
		
	def makeprocess(self,app,action):
		return Process(["sudo","control",app,action])
	
if(__name__=="__main__"):
	import sys
	from asyncproc import Process
	from select import select
	
	def datawaiting(socket):
		return select([socket], [], [], .1) == ([socket], [], [])
	
	def xmlaction(app,action):
		log("Action! "+app+action)
		if(app+action in running):
			return "Command already running"
		else:
			running[app+action]={
				'proc':makeprocess(app,action),
				'buffer':'',
				'last':int(time.time()),
				'done':False
			}
			return "Command started"
	def xmlrcmd(app,action):
		log("RCMD! "+app+action)
		try:
			program = running[app+action]
			output = program['buffer']
			program['buffer'] = ''
			if(program['done']):
				output+="#DONE#"
				del running[app+action]
			return output
		except KeyError:
			return "Command not running"
	
	# Restrict to a particular path.
	class RequestHandler(SimpleXMLRPCRequestHandler):
		rpc_paths = ('/RPC2',)

	# Create server
	server = SimpleXMLRPCServer(("localhost", port),requestHandler=RequestHandler)
	# server.register_introspection_functions()


	server.register_function(xmlaction, 'action')
	server.register_function(xmlrcmd,   'rcmd')
	
	
	
	# This informs the action function that it is running
	log("Running")

		
	running={}
	while(True):
		if(datawaiting(server.fileno())):
			log("Handled request.")
			server.handle_request()
		
		expired=[]
		for context in running:
			program=running[context]
			# check to see if process has ended
			poll = program['proc'].wait(os.WNOHANG)
			if(poll == None):
				# It hasn't ended, update it's last seen time
				program['last']=int(time.time())
			else:
				program['done']=True
				if(int(time.time())-program['last'] > 20):
					# Been too long after it ended, destroy the buffer
					log("Program "+context+" expired.")
					# Mark it for deletion
					expired.append(context)
					# Don't attempt to read it's shit, it's over
					continue
			
			# store any new output
			out = program['proc'].read()
			if out != "":
				log("Program "+context+" outputted "+out)
				program['buffer']+=out
		
		for item in expired:
			del running[item]
		
		if(len(running)==0):
			log("All programs expired, quitting")
			# Remove the pid...
			try:
				os.remove('/var/run/applications/applications.pid')
			except OSError:
				pass
			break
			
