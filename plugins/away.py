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

import dbus

plugin_info = (
	"Sets auto-away.",
	"1.0",
	"Michael Kuhn"
)

class away (sushi.Plugin):

	def __init__ (self):
		sushi.Plugin.__init__(self, "away")

		bus = dbus.SessionBus(mainloop=dbus.mainloop.glib.DBusGMainLoop())

		if not bus:
			return

		try:
			self.handler = bus.add_signal_receiver(
				self.status_changed_cb,
				"StatusChanged",
				"org.gnome.SessionManager.Presence"
			)
		except:
			self.handler = None

	def unload (self):
		if self.handler:
			self.handler.remove()

	def status_changed_cb (self, status):
		servers = self.get_bus().servers()

		for server in servers:
			if status == 3:
				self.get_bus().away(server, "Auto-away")
			else:
				self.get_bus().back(server)
