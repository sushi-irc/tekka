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
import gobject

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gettext import gettext as _

from types import NoneType
from typecheck import types

dbus_loop = DBusGMainLoop()
required_version = (1, 1, 0)
bus = None

class NoSushiError (BaseException):
	pass

class SushiWrapper (gobject.GObject):

	""" Wraps a DBus Interface to maki so if there's
		no connection, an error signal is emitted and
		can be catched by the GUI.

		Access to the underlying gobject methods is
		possible by prefixing an "g_":
		g_emit(), g_connect, ...

		The only methods available directly from
		this class are all methods beginning with an "_"
		and the "connected" property.
		All other getattr calls will be forwarded
		to the intern sushi interface.
	"""

	@types (sushi_interface = (dbus.Interface, NoneType))
	def __init__(self, sushi_interface):
		gobject.GObject.__init__(self)
		self._set_interface(sushi_interface)

	@types (connected = bool)
	def _set_connected(self, connected):
		if connected:
			self.g_emit("maki-connected")
		else:
			self.g_emit("maki-disconnected")

		self._connected = connected

	@types (interface = (dbus.Interface, NoneType))
	def _set_interface(self, interface):
		self._sushi = interface
		self._set_connected(interface != None)

	@types (title = basestring, msg = basestring)
	def _emit_error(self, title, msg):
		self.g_emit("sushi-error", title, msg)

	def __getattribute__(self, attr):

		def dummy(*args, **kwargs):
			sushi._emit_error(
				_("tekka could not connect to maki."),
				_("Please check whether maki is running."))

		def errordummy(message):
			def new(*args, **kwargs):
				sushi._emit_error(
					_("tekka could not connect to maki."),
					_("Please check whether maki is running.\n"
					"The following error occurred: %(error)s") % {
						"error": message })
			return new

		gobject_attr = False

		if attr[:2] == "g_":
			attr = attr[2:]
			gobject_attr = True

		if attr[0] == "_" or gobject_attr or attr == "connected":
			# resolve it by gobject.__getattribute__. This function
			# will call getattr as well if there is no matching
			# method in the gobject hierarchy.
			return gobject.GObject.__getattribute__(self, attr)
		else:
			if not self._sushi:
				# return a dummy which reports an error
				return dummy
			else:
				try:
					# try local methods
					return self._sushi.__getattribute__(attr)
				except AttributeError:
					# try proxy methods
					try:
						return self._sushi.__getattr__(attr)
					except dbus.DBusException, e:
						# method not found, return dummy
						return errordummy(str(e))

		raise AttributeError(attr)

	connected = property(lambda s: s._connected, _set_connected)

gobject.signal_new ("maki-connected", SushiWrapper, gobject.SIGNAL_ACTION,
	None, ())
gobject.signal_new ("maki-disconnected", SushiWrapper,
	gobject.SIGNAL_ACTION, None, ())
gobject.signal_new ("sushi-error", SushiWrapper,
	gobject.SIGNAL_ACTION, None, (str, str))

sushi = SushiWrapper(None)

myNick = {}

_shutdown_callback = None
_nick_callback = None

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
	global sushi, _shutdown_callback, _nick_callback, bus

	bus_address = os.getenv("SUSHI_REMOTE_BUS_ADDRESS")

	def bus_remote_error(exception):
		sushi._emit_error(
			_("tekka could not connect to maki."),
			_("Please check whether maki is running.\n"
			"The following error occurred: %(error)s") % {
				"error": str(exception) })

	def connect_session_bus():
		global bus, dbus_loop
		try:
			return dbus.SessionBus(mainloop=dbus_loop)
		except DBusException, e:
			sushi._emit_error(
				_("tekka could not connect to maki."),
				_("Please check whether maki is running.\n"
				"The following error occurred: %(error)s") % {
					"error": str(e) })
			return None

	if bus_address:
		try:
			bus = dbus.connection.Connection(bus_address, mainloop=dbus_loop)
		except dbus.DBusException, e:
			bus_remote_error(e)
			bus = connect_session_bus()

			if bus == None:
				return False

	else:
		bus = connect_session_bus()

		if bus == None:
			return False

	proxy = None
	try:
		proxy = bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
	except dbus.exceptions.DBusException, e:
		sushi._emit_error(
			_("tekka could not connect to maki."),
			_("Please check whether maki is running.\n"
			"The following error occurred: %(error)s") % {
				"error": str(e) })

	if not proxy:
		return False

	sushi._set_interface(dbus.Interface(proxy, "de.ikkoku.sushi"))

	version = tuple([int(v) for v in sushi.version()])

	if not version or version < required_version:
		version_string = ".".join([str(x) for x in required_version])

		sushi._emit_error(
			_("tekka requires a newer maki version."),
			_("Please update maki to at least version %(version)s.") % {
					"version": version_string })

		sushi._set_interface(None)
		return False

	_shutdown_callback = sushi.connect_to_signal("shutdown", _shutdownSignal)
	_nick_callback = sushi.connect_to_signal("nick", _nickSignal)

	for server in sushi.servers():
		fetch_own_nick(server)

	return True

def disconnect():
	global sushi, _shutdown_callback, _nick_callback
	sushi._set_interface(None)

	if _shutdown_callback:
		_shutdown_callback.remove()

	if _nick_callback:
		_nick_callback.remove()

def parse_from (from_str):
	h = from_str.split("!", 2)

	if len(h) < 2:
		return (h[0],)

	t = h[1].split("@", 2)

	if len(t) < 2:
		return (h[0],)

	return (h[0], t[0], t[1])

"""
Signals: nickchange (nick => _nickSignal)
"""

def _shutdownSignal(time):
	disconnect()

def _nickSignal(time, server, from_str, new_nick):
	nick = parse_from(from_str)[0]

	if not nick or nick == get_own_nick(server):
		cache_own_nick(server, new_nick)

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
def fetch_own_nick(server):
	from_str = sushi.user_from(server, "")
	nick = parse_from(from_str)[0]
	cache_own_nick(server, nick)

# caches the nick @nickname for server @server.
def cache_own_nick(server, nickname):
	myNick[server] = nickname

# returns the cached nick of server @server
def get_own_nick(server):
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
