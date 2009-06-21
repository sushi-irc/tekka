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

from types import NoneType
from typecheck import types

from lib.inline_dialog import InlineMessageDialog

import gui_control

dbus_loop = DBusGMainLoop()
required_version = (1, 1, 0)
bus_address = os.getenv("SUSHI_REMOTE_BUS_ADDRESS")

if bus_address:
	bus = dbus.connection.Connection(bus_address, mainloop=dbus_loop)
else:
	bus = dbus.SessionBus(mainloop=dbus_loop)


class SushiWrapper (object):

	@types (sushi_interface = (dbus.Interface, NoneType))
	def __init__(self, sushi_interface):
		self._set_interface(sushi_interface)

	@types (connected = bool)
	def _set_connected(self, connected):
		self._connected = connected

	@types (interface = (dbus.Interface, NoneType))
	def _set_interface(self, interface):
		self._set_connected(interface != None)
		self._sushi = interface

	def __getattr__(self, attr):
		def dummy(*args, **kwargs):
			dialog = InlineMessageDialog(_("tekka could not contact maki."),
				_("There's no connection to maki, so the recent "
				"action was not performed. Try to reconnect to "
				"maki to solve this problem."))
			dialog.connect("response", lambda w,i: w.destroy())
			gui_control.showInlineDialog(dialog)

		if attr[0] == "_" or attr == "connected":
			# return my attributes
			return object.__getattr__(self, attr)
		else:
			if not self._sushi:
				return dummy
			else:
				if attr in dir(self._sushi):
					# return local from Interface
					return eval("self._sushi.%s" % attr)
				else:
					# return dbus proxy method
					return self._sushi.__getattr__(attr)
		raise AttributeError(attr)

	connected = property(lambda s: s._connected, _set_connected)

sushi = SushiWrapper(None)

from signals import parse_from

myNick = {}

_connect_callbacks = []
_disconnect_callbacks = []
_shutdown_callback = None
_nick_callback = None

@types (connect_callbacks = list, disconnect_callbacks = list)
def setup(connect_callbacks, disconnect_callbacks):
	""" register initial callbacks """
	global _connect_callbacks, _disconnect_callbacks
	_connect_callbacks = connect_callbacks
	_disconnect_callbacks = disconnect_callbacks

def disable_sushi_on_fail(cmethod):
	""" decorator: disable sushi wrapper if connect fails """
	def new(*args, **kwargs):
		global sushi
		ret = cmethod(*args, **kwargs)
		if not ret:
			sushi._set_interface(None)
		return ret
	return new

@disable_sushi_on_fail
def connect():
	"""
	Connect to maki over DBus.
	Returns True if the connection attempt was succesful.
	If the attempt was successful, the sushi object's
	attribute "connected" is set to "True" and the object
	has more attributes through the dbus proxy so you
	can call dbus methods directly.
	"""
	global sushi, _shutdown_callback, _nick_callback

	proxy = None
	try:
		proxy = bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
	except dbus.exceptions.DBusException, e:
		d = InlineMessageDialog(_("tekka could not connect to maki."),
			_("Please check whether maki is running.\n"
			"The following error occured: %(error)s") % {
				"error": str(e) })
		d.connect("response", lambda d,id: d.destroy())

		gui_control.showInlineDialog(d)

	if not proxy:
		return False

	sushi._set_interface(dbus.Interface(proxy, "de.ikkoku.sushi"))

	version = tuple([int(v) for v in sushi.version()])

	if not version or version < required_version:
		version_string = ".".join([str(x) for x in required_version])

		d = InlineMessageDialog(_("tekka requires a newer maki version."),
			_("Please update maki to at least version %(version)s.") % {
					"version": version_string })
		d.connect("response", lambda d,i: d.destroy())

		gui_control.showInlineDialog(d)
		return False

	_shutdown_callback = sushi.connect_to_signal("shutdown", _shutdownSignal)
	_nick_callback = sushi.connect_to_signal("nick", _nickSignal)

	for server in sushi.servers():
		fetchOwnNick(server)

	for callback in _connect_callbacks:
		callback(sushi)

	return True

def disconnect():
	global sushi, _shutdown_callback, _nick_callback
	sushi._set_interface(None)

	if _shutdown_callback:
		_shutdown_callback.remove()

	if _nick_callback:
		_nick_callback.remove()

	for callback in _disconnect_callbacks:
		callback()

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
Commands
"""


def sendMessage(server, channel, text):
	"""
		sends a PRIVMSG to channel @channel on server @server
	"""
	text = re.sub('(^|\s)(_\S+_)(\s|$)', '\\1' + chr(31) + '\\2' + chr(31) + '\\3', text)
	text = re.sub('(^|\s)(\*\S+\*)(\s|$)', '\\1' + chr(2) + '\\2' + chr(2) + '\\3', text)

	sushi.message(server, channel, text)

# fetches the own nick for server @server from maki
def fetchOwnNick(server):
	from_str = sushi.user_from(server, "")
	nick = parse_from(from_str)[0]
	cacheOwnNick(server, nick)

# caches the nick @nickname for server @server.
def cacheOwnNick(server, nickname):
	myNick[server] = nickname

# returns the cached nick of server @server
def getOwnNick(server):
	if myNick.has_key(server):
		return myNick[server]
	return ""

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

def fetchServerInfo(server):
	# FIXME replace this
	"""
	fetch all available info of the given server from maki
	and return it as a dict
	"""
	map = {}

	if server not in sushi.server_list("", ""):
		return map

	map["servername"] = server

	for key in ("address","port","name","nick","nickserv",
				"autoconnect","nickserv_ghost","ignores",
				"commands"):
		map[key] = sushi.server_get(server, "server", key)
	return map
