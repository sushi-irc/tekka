"""
Copyright (c) 2008 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import GUI
import htmlbuffer


"""
Provides basic attributes like the outputbuffer
(default a htmlbuffer), the name of the tab and
a flag if a new message is received.
"""
class tekkaTab(object):
	def __init__(self, name, buffer=None):
		self.buffer = buffer or htmlbuffer.htmlbuffer()
		self.name = name
		self.newMessage = []

	# the output buffer
	def getBuffer(self):
		return self.buffer

	def setBuffer(self, buffer):
		self.buffer = buffer

	# the identifying name
	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	# there is a new message
	def getNewMessage(self):
		return self.newMessage

	def setNewMessage(self, type):
		if not type:
			self.newMessage = []
		else:
			try:
				self.newMessage.index(type)
			except:
				self.newMessage.append(type)

	# markup the string in due to the
	# set properties
	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name

class tekkaServer(tekkaTab):
	def __init__(self, name, buffer=None):
		tekkaTab.__init__(self, name, buffer)

		self.connected = False
		self.away = False
		self.awayMessage = ""

	# is the server connected
	def getConnected(self):
		return self.connected

	def setConnected(self,switch):
		self.connected = switch

	# we're away
	def getAway(self):
		return self.away

	def setAway(self, switch):
		self.away = switch

	def setAwayMessage(self, message):
		self.awayMessage = message

	def getAwayMessage(self):
		return self.awayMessage

	def markup(self):
		base = self.name
		if not self.connected:
			base = "("+base+")"
		if self.newMessage:
			base = "<b>"+base+"</b>"
		if self.away:
			base = "<i>"+base+"</i>"
		return base

class tekkaChannel(tekkaTab):
	def __init__(self, name, buffer=None, nicklist=None, topic=None, topicsetter=None):
		tekkaTab.__init__(self, name, buffer)

		self.nicklist = nicklist or GUI.tekkaNickListStore()
		self.topic = topic or ""
		self.topicsetter = topicsetter or ""

		self.joined = False

	# the nicks in the channel
	def getNickList(self):
		return self.nicklist

	def setNickList(self, nicklist):
		self.nicklist = nicklist

	# what's the topic
	def getTopic(self):
		return self.topic or ""

	def setTopic(self, topic):
		self.topic = topic

	# who set the topic
	def getTopicsetter(self):
		return self.topicsetter

	def setTopicsetter(self, topicsetter):
		self.topicsetter = topicsetter

	# is the channel joined?
	def getJoined(self):
		return self.joined

	def setJoined(self, switch):
		self.joined = switch

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.joined:
			base = "("+base+")"

		if "action" in self.newMessage:
			italic = True
		if "message" in self.newMessage:
			bold = True
		if "highlightmessage" in self.newMessage and "highlightaction" in self.newMessage:
			foreground = "#DDDD00"
		elif "highlightmessage" in self.newMessage:
			foreground = "#DD0000"
		elif "highlightaction" in self.newMessage:
			foreground = "#00DD00"
		
		markup = "<span "
		if italic:
			markup += "style='italic' "
		if bold:
			markup += "weight='bold' "
		if foreground:
			markup += "foreground='%s'" % foreground
		markup += ">%s</span>" % base

		return markup
