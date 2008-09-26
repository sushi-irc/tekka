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

dbus_loop = DBusGMainLoop()
bus = dbus.SessionBus(mainloop=dbus_loop)
sushi = None
myNick = {}
__connected = False

def connect():
	"""
		Connect to maki over DBus.
		Returns True if the connection attempt
		was succesful.
	"""
	global sushi

	proxy = None
	try:
		proxy = bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
	except dbus.exceptions.DBusException, e:
		print e
		print "Is maki running?"

	if not proxy:
		return False

	sushi = dbus.Interface(proxy, "de.ikkoku.sushi")

	sushi.connect_to_signal("connected", _connectedSignal)
	sushi.connect_to_signal("nick", _nickSignal)

	for server in fetchServers():
		cacheOwnNick(server,fetchOwnNick(server))

	global __connected
	__connected = True

	return True

def getConnected():
	"""
		Returns True if we are connected to maki.
	"""
	return __connected

def __noSushiMessage():
	"""
		Prints out a message that maki isn't
		running.
	"""
	print "No sushi. Is maki running?"

def shutdown(quitmsg=""):
	if not sushi:
		return __noSushiMessage()
	sushi.shutdown(quitmsg)
	global __connected
	__connected = False

"""
Signals: nickchange (nick => _nickSignal)
		 initial nick setting (connected => _connectSignal)
"""

def _connectedSignal(time, server, nick):
	cacheOwnNick(server, nick)

def _nickSignal(time, server, nick, new_nick):
	if nick == getOwnNick(server):
		cacheOwnNick(server, new_nick)

"""
Connection: connect to server
			quit server
"""

def connectServer(server):
	if not sushi:
		return __noSushiMessage()
	sushi.connect(server)

def quitServer(server, reason=""):
	if not sushi:
		return __noSushiMessage()
	sushi.quit(server,reason)

"""
Commands
"""


def sendMessage(server, channel, text):
	"""
		sends a PRIVMSG to channel @channel on server @server
	"""
	if not sushi:
		return __noSushiMessage()
	sushi.message(server, channel, text)

def fetchNicks(server, channel):
	"""
		Returns a list of nicks joined
		in channel on server.
	"""
	return sushi.channel_nicks(server,channel)

# fetches the own nick for server @server from maki
def fetchOwnNick(server):
	if not sushi:
		__noSushiMessage()
		return ""
	return sushi.own_nick(server)

# caches the nick @nickname for server @server.
def cacheOwnNick(server, nickname):
	myNick[server] = nickname

# returns the cached nick of server @server
def getOwnNick(server):
	if myNick.has_key(server):
		return myNick[server]
	return ""

# fetch all servers maki is connected to
def fetchServers():
	return sushi.servers() or []

# fetch all channels joined on server @server
def fetchChannels(server):
	return sushi.channels(server) or []

# returns all ignores set on the server
def fetchIgnores(server):
	return sushi.ignores(server)

# returns @lines lines of log for target @target on server @server
def fetchLog(server, target, lines):
	return sushi.log(server, target, lines) or []

# returns the modes set on @nick in channel @channel on
# server @server
def fetchUserChannelModes(server, channel, nick):
	return sushi.user_channel_mode(server, channel, nick)

# returns the prefix of user @nick in channel @channel
# on server @server
def fetchUserChannelPrefix(server, channel, nick):
	return sushi.user_channel_prefix(server, channel, nick)

# fetch the prefix of user @nick in channel @channel on
# server @server
def fetchPrefix(server, channel, nick):
	return sushi.user_channel_prefix(server,channel,nick)

# lookup if user @nick on server @server is away
def isAway(server, nick):
	return sushi.user_away(server, nick)

def join(server, channel, key=""):
	sushi.join(server,channel,key)

def part(server, channel, message=""):
	sushi.part(server,channel,message)

def setTopic(server, channel, topic):
	sushi.topic(server, channel, topic)

def mode(server, target, mode):
	sushi.mode(server, target, mode)

def kick(server, channel, nick, reason=""):
	sushi.kick(server, channel, nick, reason)

def nickserv(server):
	sushi.nickserv(server)

def setAway(server, message):
	sushi.away(server, message)

def setBack(server):
	sushi.back(server)

def nick(server, new_nick):
	sushi.nick(server, new_nick)

def ctcp(server, target, message):
	sushi.ctcp(server, target, message)

def action(server, channel, message):
	sushi.action(server, channel, message)

def notice(server, target, message):
	sushi.notice(server, target, message)

def oper(server, name, password):
	sushi.oper(server, name, password)

def raw(server, command):
	sushi.raw(server,command)

def ignore(server, pattern):
	sushi.ignore(server, pattern)

def unignore(server, pattern):
	sushi.unignore(server, pattern)

def list(server, channel=""):
	sushi.list(server,channel)

"""
Config, server creation, server deletion
"""

def createServer(smap):
	name = smap["servername"]
	del smap["servername"]
	for (k,v) in smap.items():
		if not v:
			sushi.server_remove(name, "server", k)
		else:
			sushi.server_set(name, "server", k, v)

def renameServer(name, newName):
	sushi.server_rename(name, newName)

def deleteServer(name):
	sushi.server_remove(name, "", "")

def fetchServerList():
	return sushi.server_list("","")

def fetchServerInfo(server):
	map = {}
	map["servername"] = server
	map["address"] = sushi.server_get(server, "server", "address")
	map["port"] = sushi.server_get(server, "server", "port")
	map["name"] = sushi.server_get(server, "server", "name")
	map["nick"] = sushi.server_get(server, "server", "nick")
	map["nickserv"] = sushi.server_get(server, "server", "nickserv")
	map["autoconnect"] = sushi.server_get(server, "server", "autoconnect")
	return map

def getChannelAutoJoin(server, channel):
	return sushi.server_get(server, channel, "autojoin")

def setChannelAutoJoin(server, channel, switch):
	sushi.server_set(server, channel, "autojoin", (switch and "true") or "false")

def getServerAutoConnect(server):
	return sushi.server_get(server, "server", "autoconnect")

def setServerAutoConnect(server, switch):
	sushi.server_set(server, "server", "autoconnect", (switch and "true") or "false")
