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

class TekkaTab(gobject.GObject):
	"""
		Provides basic attributes like the output textview,
		the name of the tab and a flag if a new message is received.

		Attributes:
		textview: the textview bound to this tag
		path: the identifying path in gtk.TreeModel
		name: the identifying name
		newMessage: a list containing message "flags"
		connected: is the tab active or not
		autoScroll: automatically scroll the textview to the end
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

	@types(name=basestring)
	def _set_name(self, name):
		self._name = name
		self.emit ("new_name", name)
	name = property(lambda x: x._name, _set_name)

	def __init__(self, name, textview=None):
		gobject.GObject.__init__(self)

		self.textview = textview
		self.path = ()
		self.name = name
		self.newMessage = []
		self.connected = False
		self.autoScroll = True
		self.input_text = ""

		self.input_history = None

	def __repr__(self):
		return "<tab '%s', path: '%s'>" % (self.name, self.path)

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

	@types(status = (str, type(None)))
	def setNewMessage(self, status):
		""" the new message status is only set if the tab is
			not active. At the moment there the following
			states are implemented:
			- "action" and "highlightaction"
			- "message" and "highlightmessage"
		"""
		if not status:
			self.newMessage = []
			self.emit ("new_message", status)
		else:
			try:
				self.newMessage.index(status)
			except ValueError:
				self.newMessage.append(status)
				self.emit ("new_message", status)

	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name

gobject.signal_new(
	"connected", TekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

""" The second parameter (type) of this signal represents
	the named type of the message (can be "action" or
	"highlight message" etc.
	new_message can be None, this means the messages
	are read.
"""
gobject.signal_new(
	"new_message", TekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_path", TekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_name", TekkaTab,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))

class TekkaServer(TekkaTab):
	"""
		A typically server tab.
	"""

	@types(msg=basestring)
	def _set_away(self, msg):
		self._away = msg
		self.emit("away", msg)

	away = property(lambda x: x._away, _set_away)

	def __init__(self, name, textview=None):
		TekkaTab.__init__(self, name, textview)

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

gobject.signal_new(
	"away",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))


class TekkaQuery(TekkaTab):
	""" Class for typical query-tabs """

	def __init__(self, name, server, textview=None):
		TekkaTab.__init__(self, name, textview)

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

class TekkaChannel(TekkaTab):
	"""
		A typically channel tab.
	"""

	@types(switch=bool)
	def _set_joined(self, switch):
		self._joined = switch
		self.emit("joined", switch)

	joined = property(lambda x: x._joined, _set_joined)

	def __init__(self, name, server, textview=None,
		nicklist=None, topic="", topicsetter=""):
		TekkaTab.__init__(self, name, textview)

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

gobject.signal_new(
	"joined", TekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN,))

