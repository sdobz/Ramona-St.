#!/usr/bin/env python
import os, subprocess, cgi, collections
import library.web as web
from struct import pack, unpack, calcsize
from cStringIO import StringIO
from pprint import pprint
from time import sleep
from time import time
from threading import Timer
from re import compile
escape=cgi.escape

# https://github.com/4poc/php-live-transcode/blob/master/stream.php

mediaroot="/var/media"
chunksize=10000
rate=0
debug=True

# Time until the ffmpeg instance expires
expiretime=5

streams=[]

# These are compiled at the end of the file
checks={
	'size':'[0-9]*x[0-9]*',
	'bitrate':'[0-9]*[mMkK]?',
	'start':'[0-9]*',
}

defaults={
	'size':'640x480',
	'bitrate':'1000k',
	'start':'0',
	'filename':'/var/media/meta.flv',
}

class stream:
	def GET(self,request):
		d(request)
		qargs=get_queryparsed()
		args=defaults.copy()
		
		d(qargs)
		
		for arg in qargs:
			value=qargs[arg]
			if not(arg in checks):
				raise web.notfound("Unknown argument: %s" % (escape(arg)))
			if(checks[arg].match(value)==None):
				raise web.notfound("Argument: %s contains an invalid format" % (escape(arg)))
			args[arg] = value
		filename=os.path.normpath(os.path.join(mediaroot,request))

		if(filename[:len(mediaroot)]!=mediaroot):
			raise web.notfound("You cannot go up directories.")

		args['filename']=filename

		if(os.path.isfile(filename)):
			web.header('Content-Type', 'video/x-flv')
			web.header('Cache-Control','no-store')
			s=flvmetainjector(args)
			check_expired()
			chunk=True
			while chunk:
				chunk=s.getchunk(chunksize)
				yield chunk
				#if(rate!=0):
				#	sleep(float(chunksize)/rate)
		elif(os.path.isdir(filename)):
			raise web.seeother("/browse/"+request)
		else:
			raise web.notfound("File: %s not found." % (filename))


def get_queryparsed():
	values = {}
	# The [1:] removes the ? from the qstring
	for key, value in cgi.parse_qs(web.ctx.query[1:]).items():
		if len(value) < 2:
			values[str(key)] = ''.join(value)
	return values

expire_timer = False
def check_expired():
	global expire_timer
	if(expire_timer):
		expire_timer.cancel()
		expire_timer=False
	
	global streams
	newstreams=[]
	for stream in streams:
		if(stream.expired()):
			stream.kill()
		else:
			newstreams.append(stream)
	streams=newstreams
	
	if(len(streams)>0):
		expire_timer = Timer(5,check_expired)
		expire_timer.start()

class streamer:
	def __init__(self,args=()):
		self.seen()
		self.args=args
		self.ffmpeg=False
		self.filename=args['filename']
		streams.append(self)
		# d('# of streamers:',len(streams))
		self.offset=0
		self.makeffmpeg()
	
	def makeffmpeg(self):
		ffmpegargs=["ffmpeg","-ss",self.args['start'],"-i",self.filename,"-b",self.args['bitrate'],"-s",self.args['size']]
		ffmpegargs+=("-async 1 -ar 44100 -ac 2 -v 0 -f flv -vcodec libx264 -preset superfast -threads 1 -").split()
		# d((" ").join(ffmpegargs))
		self.kill()

		if not(os.path.isfile(self.filename)):
			raise BaseException, 'File does not exist'
		
		self.ffmpeg=subprocess.Popen(ffmpegargs,stdout=subprocess.PIPE)
		
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
			# The extra wait gets the process status and removes the zombie process
			self.ffmpeg.wait()
		
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
	
	def getchunk(self,size):
		if(self.ffmpeg.offset==0):
			data=self.read(13)
			if(self.verifyheader(data)==False):
				return ''
		else:
			data=''
		
		while(len(data)<size):
			tag, chunk = self.readtag()
			if('ScriptDataName' in tag and tag['ScriptDataName']=='onMetaData'):
				duration=self.getduration()
				update(tag['ScriptDataValue'],self.createvalue({
					'duration':duration,
					'metadatacreator':'stream.py',
					'hasKeyframes':'true',
					#'keyframes':{
					#	'filepositions':[0,1000,2000,3000],
					#	'times':[0,1,2,3],
					#}
				}))
					
				data+=self.writetag(tag)
			else:
				data+=chunk
			
			#if('FrameType' in tag and tag['FrameType']==1):
				#d('Keyframe at offset:'+str(self.ffmpeg.offset))
		
		return data
		
	def metadata(self):
		data=self.read(13)
		if(self.verifyheader(data)==False):
			return 0
		
		while(True):
			tag, chunk = self.readtag()
			if('ScriptDataName' in tag and tag['ScriptDataName']=='onMetaData'):
				d(tag)
				break
	
	def getduration(self):
		# http://stackoverflow.com/questions/1615690/how-to-get-duration-of-video-flash-file
		args=['ffmpeg','-i',self.ffmpeg.filename]
		info=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		stdout, stderr = info.communicate()
		match = compile(r'Duration: ([\w.-]+):([\w.-]+):([\w.-]+),').search(stderr)
		# hours minutes seconds
		if(match):
			hours = float(match.group(1))
			minutes = float(match.group(2))
			seconds = float(match.group(3))
			return hours*60*60 + minutes*60 + seconds
		else:
			return 0
		
	
	def read(self,size):
		return self.ffmpeg.getchunk(size)
	
	def verifyheader(self,header):
		if(len(header)!=13):
			raise BaseException, 'FLVError: No data read.'
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
		data=self.read(11)
		u=unpack('>B 3B 3B B 3B',data)
		#          0 1  2  3 4
		# 0: 2 bit reserved, 1 bit filter, 5 bit tag type
		# 1: 3 byte DataSize
		# 2: 3 byte Timestamp (ms)
		# 3: 1 byte Additional timestamp byte? wtf?
		# 4: 3 byte StreamID
		
		tag={}
		tag['Reserved']=(u[0] & 0b11000000) >> 6
		tag['Filter']  =(u[0] & 0b00100000) >> 5
		tag['TagType'] =(u[0] & 0b00011111)
		
		# This converts 3 bytes into a 24 bit unsigned int
		tag['DataSize'] =(u[1] << 16) + (u[2] << 8) + u[3]
		
		# This number is a signed 32 bit, led by the additional timestamp bit
		tag['TimeStamp']=(u[7] << 24) + (u[4] << 16) + (u[5] << 8) + u[6]
		# Tests against '0b1000...'
		if(tag['TimeStamp']>=0x80000000):
			tag['TimeStamp']-=0x100000000
		
		tag['StreamID'] =(u[8] << 16) + (u[9] << 8) + u[10]
		
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
		StringLength = quickread('>H',strf)
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
	
	def writetag(self,tag):
		if(tag['TagType']!=18):
			raise 'Cannot write non-scriptdata tags'
		
		if(tag['Reserved'] <= 0b11):
			flags=tag['Reserved'] << 6
		else:
			raise BaseExceptions, 'FLVError: reserved too large'
		if(tag['Filter'] <= 0b1):
			flags+=tag['Filter'] << 5
		else:
			raise BaseExceptions, 'FLVError: filter not 0 or 1'
		if(tag['TagType'] <= 0b11111):
			flags+=tag['TagType']
		else:
			raise BaseExceptions, 'FLVError: tagtype too large'
		
		# Design the int
		stamp=tag['TimeStamp']
		if(stamp>=0x80000000):
			stamp-=0x100000000
		# This number is a signed 32 bit, led by the additional timestamp byte
		timestamp0 = (stamp & 0b11111111000000000000000000000000) >> 24
		timestamp  =[(stamp & 0b00000000111111110000000000000000) >> 16,
			         (stamp & 0b00000000000000001111111100000000) >> 8,
		             (stamp & 0b00000000000000000000000011111111)]

		
		streamid =[(tag['StreamID'] & 0b111111110000000000000000) >> 16,
		           (tag['StreamID'] & 0b000000001111111100000000) >> 8,
		           (tag['StreamID'] & 0b000000000000000011111111)]
		
		# Write scriptdata name and data
		body = self.writescriptdatavalue({'Type':2,'Data':tag['ScriptDataName']})
		body += self.writescriptdatavalue(tag['ScriptDataValue'])
		size = len(body)
		
		# This converts a 24 bit int to 3 1 byte chunks
		datasize = [(size & 0b111111110000000000000000) >> 16,
				    (size & 0b000000001111111100000000) >> 8,
				    (size & 0b000000000000000011111111)]
		header = pack('>B 3B 3B B 3B',flags,*list(datasize+timestamp+[timestamp0]+streamid))
		
		return header + body + pack('>I',len(header+body))
		
	def writescriptdatavalue(self,data):
		type=data['Type']
		data=data['Data']
		
		result = ''
		
		# 0 - Number (double)
		if(type==0):
			result = pack('>d',data)
			
		# 1 - Boolean (1 byte int !=0)
		if(type==1):
			result = pack('>B',data!=0)
			
		# 2 - String
		if(type==2):
			result = self.writescriptdatastring(data)
		
		# 3 - Data Object
		if(type==3):
			result = self.writescriptdataobject(data)
		
		# 4 - MovieClip - Not implemented
		# 5 - Null
		# 6 - Undefined
		# 7 - Reference
		if(type==7):
			result = pack('>H',data)
		
		# 8 - ECMA Array
		if(type==8):
			# This value is approximate? Weh?
			result = pack('>I',len(data)) + self.writescriptdataobject(data)
		
		# 9 - Object end marker, only need to return type
		# 10 - Strict Array
		if(type==10):
			ArrayLength=len(data)
			
			result += pack('>H',ArrayLength)
			for i in range(0,ArrayLength):
				result += self.writescriptdatavalue(data[i])
		
		# 11 - Date
		if(type==11):
			# Double, signed short
			result = pack('>d h',data['DateTime'],data['LocalDateTimeOffset'])
		
		# 12 - Long String - Same as a string, except use 4 bytes instead of 2
		if(type==12):
			StringLength = len(data)
			result = pack('>I '+str(StringLength)+'s',StringLength, data)
					
		return pack('>B',type) + result
	
	def writescriptdatastring(self,data):
		StringLength = len(data)
		return pack('>H '+str(StringLength)+'s',StringLength, data)
	
	def writescriptdataobject(self,data):
		result=''

		for key,value in data.iteritems():
			result += self.writescriptdatastring(key)
			result += self.writescriptdatavalue(value)
		
		result += self.writescriptdatastring('')
		result += self.writescriptdatavalue({'Type':9,'Data':0})
		return result
	
	def createvalue(self,data):
		# This can handle numbers, strings, lists (array) and dicts (object)
		if(type(data) in [int,float]):
			return {'Type':0,'Data':data}
		
		if(type(data)==str):
			return {'Type':2,'Data':data}
		
		if(type(data)==list):
			body=[]
			for item in data:
				body.append(self.createvalue(item))
			return {'Type':10,'Data':body}
		
		if(type(data)==dict):
			body={}
			for key,value in data.iteritems():
				body[key]=self.createvalue(value)
			return {'Type':3,'Data':body}
		

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

def update(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d

def d(*args):
	if(debug):
		print("DEBUG:")
		for i in args:
			pprint(i)

if(__name__=="__main__"):
	s=flvmetainjector(defaults)
	s.metadata()
