#!/usr/bin/env python
import os, subprocess
from pprint import pprint
from time import sleep
from time import time
from sys import stderr

processes=[]

# These are compiled at the end of the file
class process:
	def __init__(self,args=()):
		global processes
		self.seen()
		self.args=args
		self.proc=False
		processes.append(self)
		self.offset=0
	
	def makeprocess(self):
		self.kill()
		self.proc=subprocess.Popen(self.args,stderr=stderr,stdout=subprocess.PIPE)
		
	def getchunk(self,size):
		self.seen()
		if(self.running()):
			chunk=self.proc.stdout.read(size)
			self.offset+=len(chunk)
			return chunk
	
	def running(self):
		if(self.proc):
			return True
		else:
			return False
	
	def kill(self):
		if(self.proc):
			self.proc.kill()
		
	def seen(self):
		self.lastseen=time()
	def expired(self):
		if(time()-self.lastseen>expiretime):
			return True
		return False