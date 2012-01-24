#!/usr/bin/python

# As of 12/17/11 this module does NOT work, and doesn't conform to RamonaSt
# module format. Will be updated later --sdobz

import os, subprocess, time, library.rs_process as rs_process

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
	if(app+action in commands):
		return "Command already running"
	args=["sudo","control",app,action]
	if(block):
		return runcmd(args)
	else:
		log("Responding...")
		commands[app+action] = rs_process.process(args,60,True)
		
def rcmd(app,action):
	if not (app in apps):
		return "Invalid app"
	if not (action in actions):
		return "Invalid action"
	if not(app+action in commands):
		return "Command not running"
	prg=commands[app+action]
	output=prg.read()
	if(len(output)!=0):
		return output
	else:
		if not(prg.running()):
			del commands[app+action]
			return "#DONE#"
	
	return ""
	
def runcmd(args):
	# Run the args and return the output
	return subprocess.check_output(args)

def running(app):
	if("RUNNING" in action(app,"status",block=True)):
		return True
	return False

def log(text):
	print(text)