# coding: UTF-8
"""
Copyright (c) 2009 Michael Kuhn
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

import tekka

# tekka-specific
import config

import gobject
import gtk
import pynotify

# FIXME configurable highlight words

class pluginNotify (tekka.plugin):

	def __init__ (self, name):
		tekka.plugin.__init__(self, name)
		pynotify.init("tekka")

		self.nicks = {}
		try:
			self.pixbuf = gtk.gdk.pixbuf_new_from_file(config.get("tekka", "status_icon"))
		except:
			self.pixbuf = None

		self.get_dbus_interface().connect_to_signal("nick", self.nick_cb)

		servers = self.get_dbus_interface().servers()

		for server in servers:
			self.get_dbus_interface().nick(server, "")

		self.get_dbus_interface().connect_to_signal("message", self.message_cb)
		self.get_dbus_interface().connect_to_signal("query", self.query_cb)
		self.get_dbus_interface().connect_to_signal("action", self.action_cb)

	def nick_cb (self, timestamp, server, nick, new_nick):

		if not nick:
			self.nicks[server] = new_nick.lower()
		elif self.nicks.has_key(server) and self.nicks[server] == nick:
			self.nicks[server] = new_nick.lower()

	def message_cb (self, timestamp, server, nick, channel, message):

		if not self.nicks.has_key(server):
			return

		if message.lower().find(self.nicks[server]) >= 0:
			n = pynotify.Notification(channel, "&lt;%s&gt; %s" % (nick, gobject.markup_escape_text(message)))
			if self.pixbuf:
				n.set_icon_from_pixbuf(self.pixbuf)
			n.show()

	def query_cb (self, timestamp, server, nick, message):

		n = pynotify.Notification(nick, gobject.markup_escape_text(message))
		if self.pixbuf:
			n.set_icon_from_pixbuf(self.pixbuf)
		n.show()

	def action_cb (self, time, server, nick, channel, action):

		if not self.nicks.has_key(server):
			return

		if action.lower().find(self.nicks[server]) >= 0:
			n = pynotify.Notification(channel, "%s %s" % (nick, gobject.markup_escape_text(action)))
			if self.pixbuf:
				n.set_icon_from_pixbuf(self.pixbuf)
			n.show()

	def plugin_info(self):
		return ("Notifies on highlight.", "1.0")

def load ():
	np = pluginNotify("notify")
