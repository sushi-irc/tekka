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

import os
import re

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gettext import gettext as _

from typecheck import types
from signals import parse_from

import gui_control

dbus_loop = DBusGMainLoop()
required_version = (1, 1, 0)
bus_address = os.getenv("SUSHI_REMOTE_BUS_ADDRESS")
if bus_address:
	bus = dbus.bus.BusConnection(bus_address, mainloop=dbus_loop)
else:
	bus = dbus.SessionBus(mainloop=dbus_loop)
sushi = None
myNick = {}

_shutdown_callback = None
_nick_callback = None
_callbacks = []
__connected = False

@types (connect_callbacks = list, disconnect_callbacks = list)
def setup(connect_callbacks, disconnect_callbacks):
	global _connect_callbacks, _disconnect_callbacks
	_connect_callbacks = connect_callbacks
	_disconnect_callbacks = disconnect_callbacks

def connect():
	"""
		Connect to maki over DBus.
		Returns True if the connection attempt
		was succesful.
	"""
	global sushi, _shutdown_callback, _nick_callback

	proxy = None
	try:
		proxy = bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
	except dbus.exceptions.DBusException, e:
		d = gui_control.InlineMessageDialog(_("Can't etablish connection to maki:"),
			_("%(error_message)s\n\nIs maki running?") % {
				"error_message": str(e)})
		gui_control.showInlineDialog(d)
		d.connect("response", lambda d,id: d.destroy())

	if not proxy:
		return False

	sushi = dbus.Interface(proxy, "de.ikkoku.sushi")

	version = tuple([int(v) for v in sushi.version()])

	if not version or version < required_version:
		# FIXME
		sushi = None
		return False

	_shutdown_callback = sushi.connect_to_signal("shutdown", _shutdownSignal)
	_nick_callback = sushi.connect_to_signal("nick", _nickSignal)

	for server in fetchServers():
		fetchOwnNick(server)

	global __connected
	__connected = True

	for callback in _connect_callbacks:
		callback(sushi)

	return True

def disconnect():
	global __connected, sushi, _shutdown_callback, _nick_callback
	__connected = False
	sushi = None

	if _shutdown_callback:
		_shutdown_callback.remove()

	if _nick_callback:
		_nick_callback.remove()

	for callback in _disconnect_callbacks:
		callback()

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
"""

def _shutdownSignal(time):
	disconnect()

def _nickSignal(time, server, from_str, new_nick):
	nick = parse_from(from_str)[0]

	if not nick or nick == getOwnNick(server):
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

	text = re.sub('(^|\s)(_\S+_)(\s|$)', '\\1' + chr(31) + '\\2' + chr(31) + '\\3', text)
	text = re.sub('(^|\s)(\*\S+\*)(\s|$)', '\\1' + chr(2) + '\\2' + chr(2) + '\\3', text)

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
		return
	sushi.nick(server, "")

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
		if v:
			sushi.server_set(name, "server", k, v)

def applyServerInfo(smap):
	""" get a dictionary, search for the servername to edit
	and apply the values for the keys to the server.
	Note: smap[servername] will be removed """

	name = smap["servername"]
	del smap["servername"]

	for (k,v) in smap.items():
		sushi.server_set(name, "server", k, v)

def renameServer(name, newName):
	sushi.server_rename(name, newName)

def deleteServer(name):
	sushi.server_remove(name, "", "")

def fetchServerList():
	return sushi.server_list("","")

def fetchServerInfo(server):
	"""
	fetch all available info of the given server from maki
	and return it as a dict
	"""
	map = {}

	if server not in fetchServerList():
		return map

	map["servername"] = server

	for key in ("address","port","name","nick","nickserv",
				"autoconnect","nickserv_ghost","ignores",
				"commands"):
		map[key] = sushi.server_get(server, "server", key)
	return map

def getChannelAutoJoin(server, channel):
	return sushi.server_get(server, channel, "autojoin")

def setChannelAutoJoin(server, channel, switch):
	sushi.server_set(server, channel, "autojoin", str(switch).lower())

def getServerAutoConnect(server):
	return sushi.server_get(server, "server", "autoconnect")

def setServerAutoConnect(server, switch):
	sushi.server_set(server, "server", "autoconnect", str(switch).lower())
