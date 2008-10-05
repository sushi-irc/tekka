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

import tekka

class pluginNP(tekka.plugin):

	def __init__(self, name):
		tekka.plugin.__init__(self, name)

		self.register_command("np", self.np_command)

	def np_command(self, currentServer, currentTab, args):
		try:
			import mpd

			client = mpd.MPDClient()
			client.connect("localhost", 6600)

			data = {"artist":"N/A","title":"N/A","album":"N/A"}
			data.update(client.currentsong())

			fstring = "np: %(artist)s - %(title)s" % data

			self.get_dbus_interface().message(currentServer.name, currentTab.name, fstring)

			client.disconnect()

			return
		except:
			pass

		try:
			import os
			from xdg.BaseDirectory import xdg_config_home

			f = open(os.path.join(xdg_config_home, "decibel-audio-player", "now-playing.txt"))
			s = f.read().replace("\n", " ")
			f.close()

			self.get_dbus_interface().message(currentServer.name, currentTab.name, "np: %s" % (s))

			return
		except:
			pass

	def plugin_info(self):
		return ("Writes the current playing song to the channel after typing /np", "0.1")

def load():
	np = pluginNP("np")
