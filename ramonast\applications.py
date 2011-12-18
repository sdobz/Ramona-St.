#!/usr/bin/python

# List the acceptable applications

applications=[]

class BaseApplication:
    def __init__(self,name,url,description):
        self.pretty_name=name
        self.url=url
        self.description=description
        
applications.append(BaseApplication('SickBeard','sickbeard','A Psyk Berd'))
applications.append(BaseApplication('Application Control','appcontrol','A Psyk Berd'))