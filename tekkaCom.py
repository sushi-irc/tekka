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

# TODO: add shutdown signal

import dbus
from dbus.mainloop.glib import DBusGMainLoop

class tekkaCom(object):
	def __init__(self, config):
		dbus_loop = DBusGMainLoop()
		self.bus = dbus.SessionBus(mainloop=dbus_loop)
		self.proxy = None
		self.config = config

		self.myNick = {}

	# connect to maki over dbus
	def connect_maki(self):
		
		try:
			self.proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
		except dbus.exceptions.DBusException, e:
			print e
			print "Is maki running?"
			
		if not self.proxy:
			return False

		self.bus.add_signal_receiver(self._connectedSignal, "connected")
		self.bus.add_signal_receiver(self._nickSignal, "nick")

		for server in self.fetch_servers():
			self.cache_own_nick(server,self.fetch_own_nick(server))

		return True

	def __no_proxy_message(self):
		print "No proxy. Is maki running?"

	def get_bus(self):
		return self.bus

	def get_proxy(self):
		return self.proxy

	def get_config(self):
		return self.config

	"""
	Signals: nickchange
			 initial nick setting
	"""

	def _connectedSignal(self, time, server, nick):
		self.cache_own_nick(server, nick)

	def _nickSignal(self, time, server, nick, new_nick):
		if nick == self.get_own_nick(server):
			self.cache_own_nick(server,new_nick)

	"""
	Connection: connect to server
				quit server
	"""

	def connect_server(self, server):
		if not self.proxy:
			self.__no_proxy_message()
			return
		self.proxy.connect(server)

	def quit_server(self, server, reason=""):
		self.proxy.quit(server,reason)

	"""
	Commands
	"""

	# sends a PRIVMSG to channel @channel on server @server
	def send_message(self, server, channel, text):
		self.proxy.message(server, channel, text)
	
	# fetch all nicks in @channel on server @server
	def fetch_nicks(self, server, channel):
		return self.proxy.nicks(server,channel) or []

	# fetches the own nick for server @server from maki
	def fetch_own_nick(self, server):
		if not self.proxy:
			self.__no_proxy_message()
			return None
		return self.proxy.own_nick(server)
	
	# caches the nick @nickname for server @server.
	def cache_own_nick(self, server, nickname):
		self.myNick[server] = nickname

	# returns the cached nick of server @server
	def get_own_nick(self, server):
		if self.myNick.has_key(server):
			return self.myNick[server]
		return None

	# fetch all servers maki is connected to
	def fetch_servers(self):
		return self.proxy.servers() or []

	# fetch all channels joined on server @server
	def fetch_channels(self, server):
		return self.proxy.channels(server) or []

	# requests a topic-signal-emmit for channel @channel on
	# server @server
	def request_topic(self, server, channel):
		return self.proxy.topic(server,channel,"")

	# fetch the prefix of user @nick in channel @channel on
	# server @server
	def fetch_prefix(self, server, channel, nick):
		return self.proxy.user_channel_prefix(server,channel,nick)

	# lookup if user @nick on server @server is away
	def is_away(self, server, nick):
		return self.proxy.user_away(server, nick)

	"""
	Config, server creation, server deletion
	"""

	def create_server(self, smap):
		domain = "servers/%s" % smap["servername"]
		del smap["servername"]
		for (k,v) in smap.items():
			if not v:
				self.proxy.sushi_remove(domain, "server", k)
			else:
				self.proxy.sushi_set(domain, "server", k, v)

	def delete_server(self, name):
		domain = "servers/%s" % name
		self.proxy.sushi_remove(domain, "", "")

	def fetch_serverlist(self):
		return self.proxy.sushi_list("servers","","")
	
	def fetch_serverinfo(self, server):
		map = {}
		domain = "servers/%s" % server
		map["servername"] = server
		map["address"] = self.proxy.sushi_get(domain, "server", "address")
		map["port"] = self.proxy.sushi_get(domain, "server", "port")
		map["name"] = self.proxy.sushi_get(domain, "server", "name")
		map["nick"] = self.proxy.sushi_get(domain, "server", "nick")
		map["nickserv"] = self.proxy.sushi_get(domain, "server", "nickserv")
		map["autoconnect"] = self.proxy.sushi_get(domain, "server", "autoconnect")
		return map

	def get_channel_autojoin(self, server, channel):
		return self.proxy.sushi_get("servers/"+server, channel, "autojoin")

	def set_channel_autojoin(self, server, channel, switch):
		self.proxy.sushi_set("servers/"+server, channel, "autojoin", switch and "true" or "false")

if __name__ == "__main__":
	print "testing"
	test = tekkaCom()
