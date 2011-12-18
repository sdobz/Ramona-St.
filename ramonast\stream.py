#!/usr/bin/env python
import os, library.web, subprocess
from struct import pack, unpack, calcsize
from cStringIO import StringIO
from pprint import pprint
from time import sleep
from time import time
from sys import stderr
import cgi
escape=cgi.escape
from re import compile

# https://github.com/4poc/php-live-transcode/blob/master/stream.php

mediaroot="/var/media"
chunksize=10000
rate=50000
debug=True

# Time until the ffmpeg instance expires
expiretime=5

streams=[]

# These are compiled at the end of the file
checks={
	's':'[0-9]*x[0-9]*',
	'maxrate':'[0-9]*[mMkK]?',
	'start':'[0-9]*',
}

defaults={
	's':'640x480',
	'bitrate':'1000000',
	'start':'0',
}

class stream:
	def GET(self,request):
		qargs=get_queryparsed()
		
		request=request.split("/")
		if('start' in qargs):
			# Prepend the start parameter into the default args parsing
			request.insert(0,qargs['start'])
			request.insert(0,'start')
		
		args=defaults.copy()
		while(request[0] in args and len(request)>1):
			arg=request.pop(0)
			value=request.pop(0)
			if(checks[arg].match(value)==None):
				raise web.notfound("Argument: %s contains an invalid format" % (escape(arg)))
			args[arg] = value
		filename=os.path.normpath(os.path.join("/var/media/",*request))

		if(filename[:len(mediaroot)]!=mediaroot):
			raise web.notfound("You cannot go up directories.")
		
		#args['filename']=filename
		#yield '<h1>Arguments:</h1>'
		#yield '<table><tr><td>Name</td><td>value</td></tr>'
		#for k in args:
		#	yield '<tr><td>%s</td><td>%s</td></tr>' % (escape(k),escape(args[k]))
		#yield '</table>'

		if(os.path.isfile(filename)):
			startpos=int(args['start'])
			web.header('Content-Type', 'video/x-flv')
			web.header('Cache-Control','no-store')
			s=streamer()
			s.makeffmpeg()
			chunk=True
			while chunk:
				chunk=s.getchunk(chunksize)
				yield chunk
				#if(rate!=0):
				#	sleep(float(chunksize)/rate)
		else:
			raise web.notfound("File: %s not found." % (filename))
	

	def _close(*args):
		print(args)

def get_queryparsed():
	values = {}
	# The [1:] removes the ? from the qstring
	for key, value in cgi.parse_qs(web.ctx.query[1:]).items():
		if len(value) < 2:
			values[str(key)] = ''.join(value)
	return values

class streamer:
	def __init__(self,args=()):
		self.seen()
		self.args=args
		self.ffmpeg=False
		streams.append(self)
		self.offset=0
	
	def makeffmpeg(self):
		ffmpegargs=("ffmpeg -ss "+str(0)+" -i /var/media/golfers.flv -async 1 -b "+"1000k"+" -s "+"640x480"+" -ar 44100 -ac 2 -v 0 -f flv -vcodec libx264 -preset superfast -threads 1 -").split()
		self.kill()

		self.ffmpeg=subprocess.Popen(ffmpegargs,stderr=stderr,stdout=subprocess.PIPE)
		
	def getchunk(self,size):
		self.seen()
		if(self.running()):
			self.offset+=size
			return self.ffmpeg.stdout.read(size)
	
	def running(self):
		if(self.ffmpeg):
			return True
		else:
			return False
	
	def kill(self):
		if(self.ffmpeg):
			self.ffmpeg.kill()
		
	def seen(self):
		self.lastseen=time()
	def expired(self):
		if(time()-self.lastseen>expiretime):
			return True
		return False

class flvmetainjector:
	# Based off of the flv spec, pg 68:
	# http://download.macromedia.com/f4v/video_file_format_spec_v10_1.pdf
	def __init__(self,args=()):
		self.ffmpeg=streamer(args)
		self.ffmpeg.makeffmpeg()
		self.injected=False
		self.hasaudio=False
		self.hasvideo=False
	
	def injectstart(self,size):
		data=self.read(13)
		
		if(self.verifyheader(data)==False):
			return 0
		
		while(self.injected==False):
			tag, chunk = self.readtag()
			if('ScriptDataName' in tag and tag['ScriptDataName']=='onMetaData'):
				self.injected=True
				
				data+=chunk
			else:
				data+=chunk
		
		return data
	
	def getchunk(self,size):
		if(self.injected):
			return self.injectstart(size)
		else:
			return self.read(size)
	
	def read(self,size):
		return self.ffmpeg.getchunk(size)
				
	def verifyheader(self,header):
		if(len(header)!=13):
			raise 'FLVError'
		unpacked=unpack('>3s B B I I',header)
		FLVsignature=unpacked[0]
		#d("Sig: ",FLVsignature)
		FLVversion=unpacked[1]
		#d("Version: ",FLVversion)
		# First 5 bits
		ReservedFlag1=(unpacked[2] & 0b11111000) >> 3
		#d("Reserved: ",ReservedFlag1)
		# 6th bit
		self.hasaudio=(unpacked[2] & 0b00000100) >> 2
		#d("Hasaudio: ",self.hasaudio)
		# 7th bit
		ReservedFlag2=(unpacked[2] & 0b00000010) >> 1
		#d("Reserved: ",ReservedFlag2)
		# 8th bit
		self.hasvideo=(unpacked[2] & 0b00000001)
		#d("Hasvideo: ",self.hasvideo)
		HeaderLength=unpacked[3]
		#d("Header Length: ",HeaderLength)
		TagSize=unpacked[4]
		
		if(FLVsignature!="FLV"):
			raise BaseException, 'FLVError: Signature does not match flv file'
			return False
		if(FLVversion!=1):
			raise BaseException, 'FLVError: FLV version number '+str(FLVversion)+' not supported'
			return False
		if(ReservedFlag1!=0 or ReservedFlag2!=0):
			raise BaseException, 'FLVError: Reserved flags not 0'
			return False
		if(HeaderLength!=9):
			raise BaseException, 'FLVError: Header length not 9'
			return False
		if(TagSize!=0):
			raise BaseException, 'FLVError: First Tag Size not 0'
			return False
		return True
		
	def readtag(self):
		# Note: I am not sure on my handling of timestamp values larger than 24 bits
		# (16 777 215 / 1 000) / 60 = 279.62025 minutes
		# Should be a 4 byte previous tag length and 11 bytes of tag header
		data=self.read(4+11)
		u=unpack('>B 3B 3B B 3B',data)
		#          1 2  3  4 5
		# 1: 2 bit reserved, 1 bit filter, 5 bit tag type
		# 2: 3 byte DataSize
		# 3: 3 byte Timestamp (ms)
		# 4: 1 byte Additional timestamp byte? wtf?
		# 5: 3 byte StreamID
		
		tag={}
		tag['PrevTagSize']=u[0]
		
		tag['Reserved']=(u[1] & 0b11000000) >> 6
		tag['Filter']  =(u[1] & 0b00100000) >> 5
		tag['TagType'] =(u[1] & 0b00011111)
		
		# This converts 3 bytes into a 24 bit unsigned int
		tag['DataSize'] =(u[2] << 16) + (u[3] << 8) + u[4]
		
		# This number is a signed 32 bit, led by the additional timestamp bit
		tag['TimeStamp']=(u[8] << 24) + (u[5] << 16) + (u[6] << 8) + u[7]
		# Tests against '0b1000...'
		if(tag['TimeStamp']>=0x80000000):
			tag['TimeStamp']-=0x100000000
		
		tag['StreamID'] =(u[9] << 16) + (u[10] << 8) + u[11]
		
		if(tag['Reserved']!=0):
			raise BaseException, 'FLVError: Reserved is not 0'
		if(tag['Filter']!=0):
			raise BaseException, 'FLVError: Filter is not 0, no encrypted files allowed'
		if(tag['TagType'] not in [8,9,18]):
			raise BaseException, 'FLVError: Unknown TagType: '+str(tag['TagType'])
		if(tag['StreamID']!=0):
			raise BaseException, 'FLVError: StreamID is not 0'
		if(tag['Filter']!=0):
			raise BaseException, 'FLVError: Filter is not 0, no encrypted files allowed. Data WILL be wrong.'
		
		bodysize = tag['DataSize']

		if(tag['TagType']==8):
			part, chunk=self.readaudioheader()
			tag.update(part)
			data+=chunk
			bodysize-=len(chunk)
		if(tag['TagType']==9):
			part, chunk=self.readvideoheader()
			tag.update(part)
			data+=chunk
			bodysize-=len(chunk)
		
		
		# To be fully spec compliant:
		# EncryptionHeader and FilterParams need to be implemented here
		
		body = self.read(bodysize)
		data += body
		
		if(tag['TagType']==18):
			strf=StringIO(body)
			
			name=self.parsescriptdatavalue(strf)
			if(name['Type']!=2):
				raise BaseException, 'FLVError: ScriptDataName.Type is not string'
			tag['ScriptDataName']=name['Data']
			
			tag['ScriptDataValue']=self.parsescriptdatavalue(strf)
			
			strf.close()
		
		tag['TagSize'], chunk = quickread_d('>I',self)
		data += chunk
		return tag, data
	
	def readaudioheader(self):
		data=''
		tag={}
		# Audio data tag
		v, chunk=quickread_d('>B',self)
		data+=chunk
		
		tag['SoundFormat']=(v & 0b11110000) >> 4
		tag['SoundRate']  =(v & 0b00001100) >> 2
		tag['SoundSize']  =(v & 0b00000010) >> 1
		tag['SoundType']  =(v & 0b00000001)
		
		if(tag['SoundFormat']==10):
			# AAC has one more byte
			v, chunk=quickread_d('>B',self)
			data+=chunk
			
			tag['AACPacketType']=v
		
		return tag, data
	
	def readvideoheader(self):
		data=''
		tag={}
		# Video data tag
		v, chunk=quickread_d('>B',self)
		data+=chunk
		
		tag['FrameType']=(v & 0b11110000) >> 4
		tag['CodecID']  =(v & 0b00001111)
		
		if(tag['CodecID']==7):
			# AVC has 4 more bytes
			chunk=self.read(4)
			data+=chunk
			u=unpack('>B 3B',chunk)
			
			tag['AVCPacketType']=u[0]
			
			# This is signed
			tag['CompositionTime']=(u[1] << 16) + (u[2] << 8) + u[3]
			# If the first bit is 1 it is negative
			if(tag['CompositionTime']>=0x800000):
				tag['CompositionTime']-=0x1000000
			
			if(tag['AVCPacketType']!=1 and tag['CompositionTime']!=0):
				raise BaseException, 'FLVError: AVC Packet Type and Composition Time don\'t match'
		
		return tag, data
	
	def parsescriptdatavalue(self,strf):
		tag={}
		# Script data tag
		tag['Type'] = quickread('>B',strf)
		
		# 0 - Number (double)
		if(tag['Type']==0):
			tag['Data']=quickread('>d',strf)
			
		# 1 - Boolean (1 byte int !=0)
		if(tag['Type']==1):
			tag['Data']=quickread('>B',strf)
			tag['Data']=(tag['Data']!=0)
			
		# 2 - String
		if(tag['Type']==2):
			tag['Data']=self.parsescriptdatastring(strf)
		
		# 3 - Data Object
		if(tag['Type']==3):
			tag['Data']=self.parsescriptdataobject(strf)
		
		# 4 - MovieClip - Not implemented
		# 5 - Null
		# 6 - Undefined
		# 7 - Reference
		if(tag['Type']==7):
			tag['Data']=quickread('>H',strf)
		
		# 8 - ECMA Array
		if(tag['Type']==8):
			# This value is approximate? Weh?
			Length = quickread('>I',strf)
			# Otherwise exactly the same as an object.
			tag['Data']=self.parsescriptdataobject(strf)
		
		# 9 - Object end marker, only need to return type
		# 10 - Strict Array
		if(tag['Type']==10):
			ArrayLength=quickread('>H',strf)
			# Read ArrayLength
			tag['Data']=[]
			for i in range(0,ArrayLength):
				tag['Data'].append(self.parsescriptdatavalue(strf))
		
		# 11 - Date
		if(tag['Type']==11):
			# Double, signed short
			u=unpack('>d h',strf.read(10))
			tag['Data']={
				'DateTime':u[0],
				'LocalDateTimeOffset':u[1]
			}
		
		# 12 - Long String - Same as a string, except use 4 bytes instead of 2
		if(tag['Type']==12):
			StringLength = quickread('>I',strf)
			if(StringLength==0):
				tag['Data']=''
			else:
				tag['Data']=strf.read(StringLength)
			
		return tag
	
	def parsescriptdatastring(self,strf):
		StringLength = unpack('>H',strf.read(2))[0]
		if(StringLength==0):
			return ''
		return strf.read(StringLength)
	
	def parsescriptdataobject(self,strf):
		properties={}
		while(True):
			key=self.parsescriptdatastring(strf)
			value=self.parsescriptdatavalue(strf)
			if(value['Type']==9):
				# 9 is the object end marker
				break
			properties[key]=value
		return properties
	
for k in checks:
	checks[k]=compile("^"+checks[k]+"$")


# This function will determine how much data to pull from the format,
# 'read' it from source, and unpack it, then return the first value
# From the struct library.
# > indicates bigendian
# 	c	char			1
#	B	unsigned char	1
#	h	signed short	2
#	H	unsigned short	2
#	i	signed int		4
#	I	unsigned int	4
#	d	double			8
def quickread(format,source):
	size=calcsize(format)
	data=source.read(size)
	return unpack(format,data)[0]
def quickread_d(format,source):
	size=calcsize(format)
	data=source.read(size)
	return unpack(format,data)[0], data

def d(*args):
	if(debug):
		print("DEBUG:")
		for i in args:
			pprint(i)

if(__name__=="__main__"):
	s=flvmetainjector()
	s.getchunk(1000)
