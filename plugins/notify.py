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

import sushi

# tekka-specific
import tekka.config as config
import tekka.gui as gui

import gobject
import gtk
import pynotify
import string

# FIXME configurable highlight words

plugin_info = (
	"Notifies on highlight.",
	"1.1",
	"Michael Kuhn"
)

plugin_options = (
	("targets", "Targets to notify about (e.g. Freenode:#sushi-irc)",
	 sushi.TYPE_STRING, ""),
)


class notify (sushi.Plugin):

	def __init__ (self):
		sushi.Plugin.__init__(self, "notify")

		pynotify.init("tekka")

		self.caps = pynotify.get_server_caps()

		try:
			self.pixbuf = gtk.icon_theme_get_default().load_icon("tekka",64,0)
		except:
			self.pixbuf = None

		# FIXME
		self.connect_signal("message", self.message_cb)
		self.connect_signal("action", self.action_cb)

	def unload (self):
		self.disconnect_signal("message", self.message_cb)
		self.disconnect_signal("action", self.action_cb)

	def notify (self, subject, body):
		if gui.mgmt.has_focus():
			return

		notification = pynotify.Notification(subject, body)

		if self.pixbuf:
			notification.set_icon_from_pixbuf(self.pixbuf)

		if "append" in self.caps:
			notification.set_hint_string("append", "allowed")

		if "x-canonical-append" in self.caps:
			notification.set_hint_string("x-canonical-append", "allowed")

		notification.show()

	def escape (self, message):
		# Bold
		message = message.replace(chr(2), "")
		# Underline
		message = message.replace(chr(31), "")

		message = gobject.markup_escape_text(message)

		return message

	def has_highlight(self, text, needle):
		punctuation = string.punctuation + " \n\t"
		needle = needle.lower()
		ln = len(needle)
		for line in text.split("\n"):
			line = line.lower()
			i = line.find(needle)
			if i >= 0:
				if (line[i-1:i] in punctuation
				and line[ln+i:ln+i+1] in punctuation):
					return True
		return False

	def build_tab_name(self, server, target):
		return "%s:%s" % (server, target)

	def notify_target(self, server, target):
		""" return True if the user wants to be notified about text in
			server/target.
		"""
		return self.build_tab_name(server,target) in self.get_config(
			"targets").split(",")

	def message_cb (self, timestamp, server, from_str, target, message):
		nick = from_str.split("!")[0]
		own_nick = self.get_nick(server)

		if own_nick:
			own_nick = own_nick.lower()

		if not own_nick:
			return
		elif own_nick == nick.lower():
			return

		def in_notify():
			self.notify(target, "&lt;%s&gt; %s" % (
				nick,
				self.escape(message)))

		if own_nick == target.lower():
			self.notify(nick, self.escape(message))
		elif self.has_highlight(message, own_nick):
			in_notify()
		elif self.notify_target(server, target):
			self.notify("%s:%s:%s" % (server, target, nick),
						self.escape(message))
		else:
			for word in config.get_list("chatting","highlight_words",[]):
				if self.has_highlight(message, word):
					in_notify()
					break

	def action_cb (self, time, server, from_str, target, action):
		nick = from_str.split("!")[0]
		own_nick = self.get_nick(server)

		if own_nick:
			own_nick = own_nick.lower()

		if not own_nick:
			return
		elif own_nick == nick.lower():
			return

		def in_notify():
			self.notify(target, "%s %s" % (nick, self.escape(action)))

		if own_nick == target.lower():
			self.notify(nick, self.escape(action))
		elif self.has_highlight(action, own_nick):
			in_notify()
		elif self.notify_target(server, target):
			self.notify("%s:%s:%s" % (server, target, nick),
						self.escape(action))
		else:
			for word in config.get_list("chatting","highlight_words",[]):
				if self.has_highlight(action, word):
					in_notify()
					break
