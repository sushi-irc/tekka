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
import config

import gobject
import gtk
import pynotify

# FIXME configurable highlight words

plugin_info = (
	"Notifies on highlight.",
	"1.0",
	"Michael Kuhn"
)

class notify (sushi.Plugin):

	def __init__ (self):
		sushi.Plugin.__init__(self, "notify")

		pynotify.init("tekka")

		self.notification = None
		self.subject = None
		self.caps = pynotify.get_server_caps()

		try:
			self.pixbuf = gtk.gdk.pixbuf_new_from_file(config.get("tekka", "status_icon"))
		except:
			self.pixbuf = None

		self.connect_signal("message", self.message_cb)
		self.connect_signal("action", self.action_cb)

	def unload (self):
		self.disconnect_signal("message", self.message_cb)
		self.disconnect_signal("action", self.action_cb)

	def notify (self, subject, body):
		if not self.notification or self.subject != subject:
			self.notification = pynotify.Notification(subject, body)

			if self.pixbuf:
				self.notification.set_icon_from_pixbuf(self.pixbuf)

			if "append" in self.caps:
				self.notification.set_hint_string("append", "allowed")

			if "x-canonical-append" in self.caps:
				self.notification.set_hint_string("x-canonical-append", "allowed")

		self.subject = subject

		self.notification.update(subject, body)
		self.notification.show()

	def escape (self, message):
		# Bold
		message = message.replace(chr(2), "")
		# Underline
		message = message.replace(chr(31), "")

		message = gobject.markup_escape_text(message)

		return message

	def message_cb (self, timestamp, server, from_str, target, message):
		nick = from_str.split("!")[0]
		own_nick = self.get_nick(server)

		if own_nick:
			own_nick = own_nick.lower()

		if not own_nick:
			return
		elif own_nick == nick.lower():
			return

		if own_nick == target.lower():
			self.notify(nick, self.escape(message))
		elif message.lower().find(own_nick) >= 0:
			self.notify(target, "&lt;%s&gt; %s" % (nick, self.escape(message)))

	def action_cb (self, time, server, from_str, target, action):
		nick = from_str.split("!")[0]
		own_nick = self.get_nick(server)

		if own_nick:
			own_nick = own_nick.lower()

		if not own_nick:
			return
		elif own_nick == nick.lower():
			return

		if own_nick == target.lower():
			self.notify(nick, self.escape(action))
		elif action.lower().find(own_nick) >= 0:
			self.notify(target, "%s %s" % (nick, self.escape(action)))
