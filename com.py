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
		self.sushi = None
		self.config = config

		self.myNick = {}

	# connect to maki over dbus
	def connectMaki(self):
		proxy = None
		try:
			proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
		except dbus.exceptions.DBusException, e:
			print e
			print "Is maki running?"

		if not proxy:
			return False

		self.sushi = dbus.Interface(proxy, "de.ikkoku.sushi")

		self.sushi.connect_to_signal("connected", self._connectedSignal)
		self.sushi.connect_to_signal("nick", self._nickSignal)

		for server in self.fetchServers():
			self.cacheOwnNick(server,self.fetchOwnNick(server))

		return True

	def __noSushiMessage(self):
		print "No sushi. Is maki running?"

	def getSushi(self):
		return self.sushi

	def getConfig(self):
		return self.config

	"""
	Signals: nickchange (nick => _nickSignal)
			 initial nick setting (connected => _connectSignal)
	"""

	def _connectedSignal(self, time, server, nick):
		self.cacheOwnNick(server, nick)

	def _nickSignal(self, time, server, nick, new_nick):
		if nick == self.getOwnNick(server):
			self.cacheOwnNick(server,new_nick)

	"""
	Connection: connect to server
				quit server
	"""

	def connectServer(self, server):
		if not self.sushi:
			self.__noSushiMessage()
			return
		self.sushi.connect(server)

	def quitServer(self, server, reason=""):
		self.sushi.quit(server,reason)

	"""
	Commands
	"""

	# sends a PRIVMSG to channel @channel on server @server
	def sendMessage(self, server, channel, text):
		self.sushi.message(server, channel, text)

	# fetch all nicks in @channel on server @server
	def fetchNicks(self, server, channel):
		return self.sushi.nicks(server,channel) or []

	# fetches the own nick for server @server from maki
	def fetchOwnNick(self, server):
		if not self.sushi:
			self.__noSushiMessage()
			return None
		return self.sushi.own_nick(server)

	# caches the nick @nickname for server @server.
	def cacheOwnNick(self, server, nickname):
		self.myNick[server] = nickname

	# returns the cached nick of server @server
	def getOwnNick(self, server):
		if self.myNick.has_key(server):
			return self.myNick[server]
		return None

	# fetch all servers maki is connected to
	def fetchServers(self):
		return self.sushi.servers() or []

	# fetch all channels joined on server @server
	def fetchChannels(self, server):
		return self.sushi.channels(server) or []

	# returns all ignores set on the server
	def fetchIgnores(self, server):
		return self.sushi.ignores(server)

	# returns @lines lines of log for target @target on server @server
	def fetchLog(self, server, target, lines):
		return self.sushi.log(server, target, lines) or []

	# returns the modes set on @nick in channel @channel on
	# server @server
	def fetchUserChannelModes(self, server, channel, nick):
		return self.sushi.user_channel_mode(server, channel, nick)

	# returns the prefix of user @nick in channel @channel
	# on server @server
	def fetchUserChannelPrefix(self, server, channel, nick):
		return self.sushi.user_channel_prefix(server, channel, nick)

	# fetch the prefix of user @nick in channel @channel on
	# server @server
	def fetchPrefix(self, server, channel, nick):
		return self.sushi.user_channel_prefix(server,channel,nick)

	# lookup if user @nick on server @server is away
	def isAway(self, server, nick):
		return self.sushi.user_away(server, nick)

	def join(self, server, channel, key=""):
		self.sushi.join(server,channel,key)

	def part(self, server, channel, message=""):
		self.sushi.part(server,channel,message)

	def setTopic(self, server, channel, topic):
		self.sushi.topic(server, channel, topic)

	def mode(self, server, target, mode):
		self.sushi.mode(server, target, mode)

	def kick(self, server, channel, nick, reason=""):
		self.sushi.kick(server, channel, nick, reason)

	def nickserv(server):
		self.sushi.nickserv(server)

	def setAway(self, server, message):
		self.sushi.away(server, message)

	def setBack(self, server):
		self.sushi.back(server)

	def nick(self, server, new_nick):
		self.sushi.nick(server, new_nick)

	def ctcp(self, server, target, message):
		self.sushi.ctcp(server, target, message)

	def action(self, server, channel, message):
		self.sushi.action(server, channel, message)

	def notice(self, server, target, message):
		self.sushi.notice(server, target, message)

	def oper(self, server, name, password):
		self.sushi.oper(server, name, password)

	def kill(self, server, nick, reason):
		self.sushi.kill(server, nick, reason)

	def raw(self, server, command):
		self.sushi.raw(server,command)

	def ignore(self, server, pattern):
		self.sushi.ignore(server, pattern)

	def unignore(self, server, pattern):
		self.sushi.unignore(server, pattern)

	def list(self, server, channel=""):
		self.sushi.list(server,channel)

	"""
	Config, server creation, server deletion
	"""

	def createServer(self, smap):
		name = smap["servername"]
		del smap["servername"]
		for (k,v) in smap.items():
			if not v:
				self.sushi.server_remove(name, "server", k)
			else:
				self.sushi.server_set(name, "server", k, v)

	def renameServer(self, name, newName):
		try:
			self.sushi.server_rename(name, newName)
		except dbus.exceptions.UnknownMethodException:
			print "server_rename not known to maki"

	def deleteServer(self, name):
		self.sushi.server_remove(name, "", "")

	def fetchServerList(self):
		return self.sushi.server_list("","")

	def fetchServerInfo(self, server):
		map = {}
		map["servername"] = server
		map["address"] = self.sushi.server_get(server, "server", "address")
		map["port"] = self.sushi.server_get(server, "server", "port")
		map["name"] = self.sushi.server_get(server, "server", "name")
		map["nick"] = self.sushi.server_get(server, "server", "nick")
		map["nickserv"] = self.sushi.server_get(server, "server", "nickserv")
		map["autoconnect"] = self.sushi.server_get(server, "server", "autoconnect")
		return map

	def getChannelAutojoin(self, server, channel):
		return self.sushi.server_get(server, channel, "autojoin")

	def setChannelAutojoin(self, server, channel, switch):
		self.sushi.server_set(server, channel, "autojoin", switch and "true" or "false")

	"""
	Shutdown
	"""

	def shutdown(self,quitmsg=""):
		self.sushi.shutdown(quitmsg)


if __name__ == "__main__":
	print "testing"
	test = tekkaCom()
