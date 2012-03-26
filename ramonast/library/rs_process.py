#!/usr/bin/env python
import os, sys, subprocess
from threading import Timer
from threading import Thread
from Queue import Queue, Empty
from time import sleep
from time import time

processes=[]
EXPIRE_RATE=1
ON_POSIX = 'posix' in sys.builtin_module_names

# These are compiled at the end of the file
class process:
	def __init__(self,args=(),expiretime=60,buffered=False):
		global processes
		self.seen()
		self.args=args
		self.proc=False
		processes.append(self)
		self.expiretime=expiretime
		
		if(buffered):
			# I dunno how this works, really, but whatever.
			# http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
			self.buffer=""
			self.proc=subprocess.Popen(self.args,stdout=subprocess.PIPE, bufsize=1, close_fds=ON_POSIX)
			self.queue=Queue()
			self.thread=Thread(target=enqueue_output, args=(self.proc.stdout, self.queue))
			self.thread.daemon=True
			self.thread.start()
		else:
			self.buffer=False
			self.proc=subprocess.Popen(self.args,stdout=subprocess.PIPE, close_fds=ON_POSIX)
		
		check_expired()
	
	def __del__(self):
		if(self.proc):
			self.proc.kill()
			self.proc.wait()
	
	def read(self,size=0):
		self.seen()
		if(self.proc):
			if(self.buffer!=False):
				# One last read
				self.readtobuffer()
				
				if(size==0):
					size = len(self.buffer)
				chunk=self.buffer[:size]
				self.buffer=self.buffer[size:]
				if(self.running() == False and len(chunk) == 0):
					# Stopped program has no new output
					return False
				return chunk
			else:
				return self.proc.stdout.read(size)
		
		return False
		
	
	def running(self):
		return program['proc'].wait(os.WNOHANG) == None
	

	def seen(self):
		self.lastseen=time()
	
	def readtobuffer(self):
		if(self.buffer!=False):
			try:
				line = self.queue.get_nowait() # or q.get(timeout=.1)
			except Empty: # No output
				pass
			else: # got line
				self.buffer+=line
	
	def expired(self):
		if(time()-self.lastseen>self.expiretime):
			return True
		return False
		
def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def command(args):
	return subprocess.Popen(args).communicate()

expire_timer = False
def check_expired():
	global expire_timer
	if(expire_timer):
		expire_timer.cancel()
		expire_timer=False
	
	global processes
	newprocesses=[]
	for proc in processes:
		if not(proc.expired()):
			newprocesses.append(proc)
		else:
			del proc
	processes=newprocesses
	
	if(len(processes)>0):
		expire_timer = Timer(EXPIRE_RATE,check_expired)
		expire_timer.start()
		
if(__name__=="__main__"):
	p=process(('/var/apps/RamonaSt/ramonast/library/slowassprogram'),8,True)
	sleep(1)
	print(p.read())
	sleep(5)
	print(p.read())
	sleep(15)
	print(p.read())
