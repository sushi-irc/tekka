# coding: UTF-8
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

from dbus import String
import gobject
from typecheck import types

class tekkaTab(gobject.GObject):
	"""
		Provides basic attributes like the outputbuffer,
		the name of the tab and a flag if a new message is received.

		Attributes:
		buffer: the output buffer
		path: the identifying path in gtk.TreeModel
		name: the identifying name
		newMessage: a list containing message "flags"
		connected: is the tab active or not
		autoScroll: automatically scroll the buffer to the end
	"""

	@types(switch=bool)
	def _set_connected(self, switch):
		self._connected=switch
		self.emit ("connected", switch)
	connected = property(lambda x: x._connected, _set_connected)

	@types(path=tuple)
	def _set_path(self, path):
		self._path = path
		self.emit ("new_path", path)
	path = property(lambda x: x._path, _set_path)

	@types(name=(str,String,unicode))
	def _set_name(self, name):
		self._name = name
		self.emit ("new_name", name)
	name = property(lambda x: x._name, _set_name)

	def __init__(self, name, buffer=None):
		gobject.GObject.__init__(self)

		self.buffer = buffer

		self.path = ()

		self.name = name
		self.newMessage = []
		self.connected = False

		self.autoScroll = True

		self.input_text = ""

		self.inputHistory = []
		self.historyPosition = -1
		self.currentHistory = ""

	def __repr__(self):
		return "<tab '%s', path: '%s'>" % (self.name, self.path)

	""" I don't know if this is required but iirc
	python is throwing the AttributeError exception if
	anyone tries to call up a function which does not exist
	in the object so we can't easily write 'if tab.is_server()'
	without the following lines of code. """
	def is_server(s):
		return False
	def is_query(s):
		return False
	def is_channel(s):
		return False

	@types(text = str)
	def set_input_text(self, text):
		self.input_text = text

	def get_input_text(self):
		return self.input_text

	def setNewMessage(self, type):
		if not type:
			self.newMessage = []
		else:
			try:
				self.newMessage.index(type)
			except:
				self.newMessage.append(type)
		self.emit ("new_message", type)

	def insertHistory(self, string):
		"""
			Inserts a new input history string.
		"""
		self.inputHistory.insert(0, string)
		if len(self.inputHistory) > 20:
			del self.inputHistory[20:]
		self.historyPosition = -1

	def getCurrentHistory(self):
		return self.currentHistory

	def setCurrentHistory(self, string):
		self.currentHistory = string

	def getNextHistory(self):
		"""
			Gets the next item in history
		"""
		if not self.inputHistory:
			return ""

		print self.historyPosition

		if self.historyPosition + 1 == len(self.inputHistory):
			return self.inputHistory[self.historyPosition]
		else:
			self.historyPosition += 1
			return self.inputHistory[self.historyPosition]

	def getPrevHistory(self):
		"""
			Gets the previous item in history
		"""

		print self.historyPosition

		if not self.inputHistory or self.historyPosition - 1 < 0:
			self.historyPosition = -1
			return ""
		else:
			self.historyPosition -= 1
			return self.inputHistory[self.historyPosition]

	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name

	def copy(self):
		"""
			Returns a copy of this tab.
		"""
		copy = tekkaTab(str(self.name))
		copy.buffer = self.buffer # XXX: Not a copy!
		copy.newMessage = list(self.newMessage)
		copy.connected = self.connected
		copy.path = self.path
		copy.autoScroll = self.autoScroll
		copy.inputHistory = list(self.inputHistory)
		copy.historyPosition = self.historyPosition

		return copy

gobject.signal_new(
	"connected", tekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

gobject.signal_new(
	"new_message", tekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_path", tekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_name", tekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))

class tekkaServer(tekkaTab):
	"""
		A typically server tab.
	"""

	@types(msg=str)
	def _set_away(self, msg):
		self._away = msg
		self.emit("away", msg)

	away = property(lambda x: x._away, _set_away)

	def __init__(self, name, buffer=None):
		tekkaTab.__init__(self, name, buffer)

		self.away = ""

	def is_server(self):
		return True

	def markup(self):
		base = self.name
		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"
		if self.newMessage:
			base = "<b>"+base+"</b>"
		if self.away:
			base = "<i>"+base+"</i>"
		return base

	def copy(self):
		copy = tekkaServer(str(self.name))
		copy.buffer = self.buffer # XXX: Not a copy!
		copy.newMessage = list(self.newMessage)
		copy.connected = self.connected
		copy.path = self.path
		copy.autoScroll = self.autoScroll
		copy.inputHistory = list(self.inputHistory)
		copy.historyPosition = self.historyPosition
		copy.away = str(self.away)
		return copy

gobject.signal_new(
	"away",
	tekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))


class tekkaQuery(tekkaTab):
	"""
		Class for typical query-tabs.
	"""
	def __init__(self, name, server, buffer=None):
		tekkaTab.__init__(self, name, buffer)

		self.server = server

	def is_query(self):
		return True

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"

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

	def copy(self):
		copy = tekkaQuery(self, str(self.name))
		copy.buffer = self.buffer # XXX: Not a copy!
		copy.newMessage = list(self.newMessage)
		copy.connected = self.connected
		copy.path = self.path
		copy.autoScroll = self.autoScroll
		copy.inputHistory = list(self.inputHistory)
		copy.historyPosition = self.historyPosition
		copy.server = str(self.server)
		return copy

class tekkaChannel(tekkaTab):
	"""
		A typically channel tab.
	"""

	@types(switch=bool)
	def _set_joined(self, switch):
		self._joined = switch
		self.emit("joined", switch)

	joined = property(lambda x: x._joined, _set_joined)

	def __init__(self, name, server, buffer=None, nicklist=None, topic="", topicsetter=""):
		tekkaTab.__init__(self, name, buffer)

		self.nickList = nicklist
		self.topic = topic
		self.topicSetter = topicsetter
		self.joined = False

		self.server = server

	def is_channel(self):
		return True

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.joined:
			base = "<span strikethrough='true'>"+base+"</span>"

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

	def copy(self):
		copy = tekkaChannel(str(self.name))
		copy.buffer = self.buffer # XXX: Not a copy!
		copy.newMessage = list(self.newMessage)
		copy.connected = self.connected
		copy.path = self.path
		copy.autoScroll = self.autoScroll
		copy.inputHistory = list(self.inputHistory)
		copy.historyPosition = self.historyPosition
		copy.nickList = self.nickList # FIXME: this is only a reference, no copy...
		copy.topic = str(self.topic)
		copy.topicSetter = str(self.topicSetter)
		copy.joined = self.joined
		copy.server = str(self.server)
		return copy


gobject.signal_new(
	"joined", tekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,))

