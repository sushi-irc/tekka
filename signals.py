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

from gettext import gettext as _

import gtk
import gobject
import logging
import string
from dbus import UInt64
import time as mtime

import com
import config

import lib.gui_control as gui
from lib import key_dialog
from lib import contrast
from lib import dcc_dialog
from lib import tab as tabs

from helper import color

from com import sushi, parse_from

from typecheck import types

signals = {}
restore_list = []

def setup():
	sushi.g_connect("maki-connected", handle_maki_connect_cb)
	sushi.g_connect("maki-disconnected", handle_maki_disconnect_cb)

"""
One should use this methods to connect to maki's
signals. This API features automatic reconnection
of the registered signals if the connection to
maki was reset.
- connect_signal(<name>,<handler>)
- disconnect_signal(<name>,<handler>)
"""

@types (signal=basestring)
def connect_signal (signal, handler):
	""" connect handler to signal """
	global signals

	if not signals.has_key (signal):
	  	signals[signal] = {}

	if signals[signal].has_key(handler):
		# no doubles
		return

	signals[signal][handler] = sushi.connect_to_signal (signal, handler)

@types (signal=basestring)
def disconnect_signal (signal, handler):
	""" disconnect handler from signal """
	global signals

	try:
		ob = signals[signal][handler]
	except KeyError:
		return
	else:
		ob.remove()
		del signals[signal][handler]

def _connect_signals():

	# Message-Signals
	connect_signal("message", userMessage_cb)
	connect_signal("notice", userNotice_cb)
	connect_signal("action", userAction_cb)
	connect_signal("away_message", userAwayMessage_cb)
	connect_signal("ctcp", userCTCP_cb)
	connect_signal("error", userError_cb)

	# action signals
	connect_signal("part", userPart_cb)
	connect_signal("join", userJoin_cb)
	connect_signal("names", userNames_cb)
	connect_signal("quit", userQuit_cb)
	connect_signal("kick", userKick_cb)
	connect_signal("nick", userNick_cb)
	connect_signal("away", userAway_cb)
	connect_signal("back", userBack_cb)
	connect_signal("mode", userMode_cb)
	connect_signal("oper", userOper_cb)

	# Server-Signals
	connect_signal("connect", serverConnect_cb)
	connect_signal("connected", serverConnected_cb)
	connect_signal("motd", serverMOTD_cb)
	connect_signal("dcc_send", dcc_send_cb)

	# Channel-Signals
	connect_signal("topic", channelTopic_cb)
	connect_signal("banlist", channelBanlist_cb)

	# Maki signals
	connect_signal("shutdown", makiShutdown_cb)

def _restore_signals():
	global restore_list

	for (signal, handler) in restore_list:
		connect_signal(signal, handler)

def handle_maki_disconnect_cb(sushi):
	global signals
	global restore_list

	for signal in signals:
		for handler in signals[signal]:
			signals[signal][handler].remove()
			restore_list.append((signal, handler))

	signals = {}

def handle_maki_connect_cb(sushi):
	""" connect to the important signals of maki
		or, if we've done that before, reconnect
		that signals (and all other registered)
	"""

	self = handle_maki_connect_cb
	try:
		self.init
	except AttributeError:
		self.init = True
	else:
		self.init = False

	if self.init:
		_connect_signals()
	else:
		_restore_signals()

	_add_servers()

@types (server = basestring)
def _setup_server(server):
	tab = gui.tabs.create_server(server)

	gui.tabs.add_tab(None, tab,
		update_shortcuts = config.get_bool("tekka","server_shortcuts"))

	return tab

def _add_servers():
	""" Adds all servers to tekka which are reported by maki. """
	# in case we're reconnecting, clear all stuff
	gui.widgets.get_widget("serverTree").get_model().clear()

	for server in sushi.servers():
		tab = _setup_server(server)
		tab.connected = True
		_add_channels(tab)

	try:
		toSwitch = gui.tabs.get_all_tabs()[1]
	except IndexError:
		return
	else:
		gui.tabs.switch_to_path(toSwitch.path)


@types (server_tab = tabs.TekkaServer)
def _add_channels(server_tab):
	"""
		Adds all channels to tekka wich are reported by maki.
	"""
	channels = sushi.channels(server_tab.name)

	for channel in channels:

		add = False
		nicks, prefixes = sushi.channel_nicks(server_tab.name, channel)

		tab = gui.tabs.search_tab(server_tab.name, channel)

		if not tab:
			tab = gui.tabs.create_channel(server_tab, channel)
			add = True

		tab.nickList.clear()
		tab.nickList.add_nicks(nicks, prefixes)

		tab.topic = sushi.channel_topic(server_tab.name, channel)
		tab.topicsetter = ""

		if gui.tabs.is_active(tab):
			gui.set_topic(gui.markup_escape(tab.topic))
			gui.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		# TODO: handle topic setter
		tab.joined = True
		tab.connected = True

		if add:
			gui.tabs.add_tab(server_tab, tab, update_shortcuts = False)
			gui.print_last_log(server_tab.name, channel)

		topic = sushi.channel_topic(server_tab.name, channel)
		_report_topic(mtime.time(), server_tab.name, channel, topic)

	gui.updateServerTreeShortcuts()

def isHighlighted (server_tab, text):
	def has_highlight(text, needle):
		punctuation = string.punctuation + " \n\t"
		ln = len(needle)
		for line in text.split("\n"):
			line = line.lower()
			i = line.find(needle)
			if i >= 0:
				if (line[i-1:i] in punctuation
				and line[ln+i:ln+i+1] in punctuation):
					return True
		return False

	highlightwords = config.get_list("chatting", "highlight_words", [])
	highlightwords.append(server_tab.nick)

	for word in highlightwords:
		if has_highlight(text, word):
			return True
	return False

@types (server = basestring, name = basestring)
def _createTab (server, name):
	""" check if tab exists, create it if not, return the tab """
	server_tab = gui.tabs.search_tab(server)
	tab = gui.tabs.search_tab(server, name)

	if not server_tab:
		raise Exception(
		"No server tab in _createTab(%s, %s)" % (server,name))

	if not tab:
		if name[0] in server_tab.support_chantypes:
			tab = gui.tabs.create_channel(server_tab, name)
		else:
			tab = gui.tabs.create_query(server_tab, name)

		tab.connected = True
		gui.tabs.add_tab(server_tab, tab)
		gui.print_last_log(server, name)

	if tab.name != name:
		# the name of the tab differs from the
		# real nick, correct this.
		tab.name = name

	return tab

def _getPrefix(server, channel, nick):
	tab = gui.tabs.search_tab(server, channel)

	if tab and tab.is_channel():
		return tab.nickList.get_prefix(nick)
	else:
		return ""

@types (tab = tabs.TekkaTab, what = basestring, own = bool)
def _hide_output(tab, what, own = False):
	""" Returns bool.
		Check if the message type determined by "what"
		shall be hidden or not.
		tab should be a TekkaServer, -Channel or -Query
	"""
	if type(tab) == tabs.TekkaChannel:
		cat = "channel_%s_%s" % (
					tab.server.name.lower(),
					tab.name.lower())
	elif type(tab) == tabs.TekkaQuery:
		cat = "query_%s_%s" % (
					tab.server.name.lower(),
					tab.name.lower())
	else:
		return False

	hide = what in config.get_list(cat, "hide", [])
	hideOwn = what in config.get_list(cat, "hide_own", [])

	return ((hide and not own)
		or (own and hideOwn)
		or (hide and own and not hideOwn))

@types (servertab = tabs.TekkaServer, tab = tabs.TekkaTab,
	what = basestring, own = bool)
def _show_output_exclusive(servertab, tab, what, own = False):
	""" Returns bool.
		Determine if the message identified by -what- shall
		be shown in tab -tab- or not.
		-servertab- is not used at the moment.
	"""
	return not _hide_output(tab, what, own = own)

""" Server callbacks """

def serverConnect_cb(time, server):
	"""
		maki is connecting to a server.
	"""
	gui.set_useable(True)

	tab = gui.tabs.search_tab(server)

	if not tab:
		tab = _setup_server(server)

	if tab.connected:
		tab.connected = False

		channels = gui.tabs.get_all_tabs(servers = [server])[1:]

		if channels:
			for channelTab in channels:
				if channelTab.is_channel():
					channelTab.joined=False
				channelTab.connected=False

	gui.serverPrint(time, server, "Connecting...")

	gui.status.set("connecting", "Connecting to %s" % server)

def serverConnected_cb(time, server):
	"""
		maki connected successfuly to a server.
	"""
	tab = gui.tabs.search_tab(server)

	if not tab:
		tab = _setup_server(server)

	tab.connected = True

	# iterate over tabs, set the connected flag to queries
	for query in [tab for tab in gui.tabs.get_all_tabs(
	servers = [server])[1:] if tab.is_query()]:
		query.connected = True

	gui.serverPrint(time, server, "Connected.")

def serverMOTD_cb(time, server, message, first_time = {}):
	""" Server is sending a MOTD.
		Channes are joined 3s after the end of the
		MOTD so at the end of the MOTD, make sure
		that the prefixes and chantypes are read
		correctly.
	"""
	if not first_time.has_key(server):
		tab = gui.tabs.search_tab(server)
		if not tab:
			tab = _setup_server(server)
		else:
			gui.tabs.update_server(tab)

		gui.status.unset("connecting")
		tab.connected = True
		first_time[server] = tab

	if not message:
		# get the prefixes for the server to make
		# sure they are correct
		tab = first_time[server]
		tab.support_prefix = sushi.support_prefix(server)
		tab.support_chantypes = sushi.support_chantypes(server)
		del first_time[server]

	else:
		gui.serverPrint(time, server, gui.escape(message),
			no_general_output = True)

""" Callbacks for channel interaction """

def _report_topic(time, server, channel, topic):
	message = _(u"• Topic for %(channel)s: %(topic)s") % {
		"channel": channel,
		"topic": gui.escape(topic) }
	gui.channelPrint(time, server, channel, message, "action",
		no_general_output = True)

def channelTopic_cb(time, server, from_str, channel, topic):
	"""
		The topic was set on server "server" in channel "channel" by
		user "nick" to "topic".
		Apply this!
	"""
	nick = parse_from(from_str)[0]
	serverTab, channelTab = gui.tabs.search_tabs(server, channel)

	if not channelTab:
		raise Exception("Channel %s does not exist but "
						"emits topic signal." % channel)

	channelTab.topic = topic
	channelTab.topicsetter = nick

	if channelTab == gui.tabs.get_current_tab():
		gui.set_topic(gui.markup_escape(topic))

	if not nick:
		# just reporting the topic.
		_report_topic(time, server, channel, topic)

	else:
		if nick == serverTab.nick:
			message = _(u"• You changed the topic to %(topic)s.")
		else:
			message = _(u"• %(nick)s changed the topic to %(topic)s.")

		gui.channelPrint(
			time, server, channel,
			message % {
				"nick": nick,
				"topic": gui.escape(topic) },
			"action")

def channelBanlist_cb(time, server, channel, mask, who, when):
	"""
		ban list signal.
	"""
	if not mask and not who and when == -1:
		gui.channelPrint(
			time, server, channel,
			"End of banlist.", "action")
	else:
		timestring = mtime.strftime(
			"%Y-%m-%d %H:%M:%S",
			mtime.localtime(when))

		gui.channelPrint(
			time,
			server,
			channel,
			"%s by %s on %s" % (
				gui.escape(mask),
				gui.escape(who),
				gui.escape(timestring)),
			"action")

""" Callbacks of maki signals """

def makiShutdown_cb(time):
	gui.myPrint("Maki is shut down!")
	gui.set_useable(False)

""" Callbacks for users """

def userAway_cb(time, server):
	"""
		maki says that we are away.
	"""
	tab = gui.tabs.search_tab(server)

	if tab:
		tab.away = "-- Not implemented yet --"


def userBack_cb(time, server):
	"""
		maki says that we are back from away being.
	"""
	tab = gui.tabs.search_tab(server)

	if tab:
		tab.away = ""

def userAwayMessage_cb(timestamp, server, nick, message):
	"""
		The user is away and the server gives us the message he left
		for us to see why he is away and probably when he's back again.
	"""
	tab = gui.tabs.get_current_tab()


	# XXX:  you can still write /msg <nick> and get an away message
	# XXX:: in the query window. This would be a more complex fix.
	try:
		tab.printed_away_message
	except AttributeError:
		print_it = True
	else:
		print_it = not tab.printed_away_message

	if print_it:
		gui.channelPrint(
			timestamp,
			server,
			nick,
			_(u"• %(nick)s is away (%(message)s).") % {
				"nick": nick,
				"message": gui.escape(message)},
			"action")


		if tab and tab.name == nick:
			tab.printed_away_message = True

def userMessage_cb(timestamp, server, from_str, channel, message):
	"""
		PRIVMSGs are coming in here.
	"""
	nick = parse_from(from_str)[0]
	server_tab = gui.tabs.search_tab(server)

	if nick.lower() == server_tab.nick.lower():
		ownMessage_cb(timestamp, server, channel, message)
		return

	elif channel.lower() == server_tab.nick.lower():
		userQuery_cb(timestamp, server, from_str, message)
		return

	message = gui.escape(message)

	if isHighlighted(server_tab, message):
		# set mode to highlight and disable setting
		# of text color for the main message (would
		# override channelPrint() highlight color)

		type = "highlightmessage"
		messageString = message
		gui.set_urgent(True)
	else:
		# no highlight, normal message type and
		# text color is allowed.

		type = "message"
		messageString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick), message)

	gui.channelPrint(timestamp, server, channel,
		"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			_getPrefix(server, channel, nick),
			color.get_nick_color(nick),
			gui.escape(nick),
			messageString,
		), type)

def ownMessage_cb(timestamp, server, channel, message):
	"""
		The maki user wrote something on a channel or a query
	"""
	_createTab(server, channel)
	nick = gui.tabs.search_tab(server).nick

	gui.channelPrint(timestamp, server, channel,
		"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt;"
		" <font foreground='%s'>%s</font>" % (
			_getPrefix(server, channel, nick),
			config.get("colors","own_nick","#000000"),
			nick,
			config.get("colors","own_text","#000000"),
			gui.escape(message)))

def userQuery_cb(timestamp, server, from_str, message):
	"""
		A user writes to us in a query.
	"""
	nick = parse_from(from_str)[0]

	_createTab(server, nick)

	gui.channelPrint(timestamp, server, nick,
		"&lt;<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			color.get_nick_color(nick),
			gui.escape(nick),
			gui.escape(message)
		), "message")

	# queries are important
	gui.set_urgent(True)

def userMode_cb(time, server, from_str, target, mode, param):
	"""
		Mode change on target from nick detected.
		nick and param are optional arguments and
		can be empty.

		As nemo:
			/mode #xesio +o nemo
		will result in:
			userMode(<time>,<server>,"nemo","#xesio","+o","nemo")
	"""

	def n_updatePrefix(tab, nick, mode):
		""" checks if the mode is a prefix-mode (e.g. +o)
			If so, the prefix of the nick `nick` in channel `channel`
			will be updated (fetched).
		"""
		if not nick:
			return

		if mode[1] in tab.server.support_prefix[0]:
			tab.nickList.set_prefix(nick,
				sushi.user_channel_prefix(tab.server.name, tab.name, nick))

			if gui.tabs.is_active(tab):
				gui.set_user_count(len(tab.nickList),
					tab.nickList.get_operator_count())

	nick = parse_from(from_str)[0]

	# nick: /mode target +mode param
	server_tab = gui.tabs.search_tab(server)

	if not nick:
		# only a mode listing
		gui.currentServerPrint(time, server,
			_("• Modes for %(target)s: %(mode)s") % {
				"target":target,
				"mode":mode},
			"action")

	else:
		actor = nick
		own = (nick == server_tab.nick)

		if own:
			actor = "You"

		tab = gui.tabs.search_tab(server, target)

		if not tab:
			# no channel/query found

			if param: param = " "+param

			if not _hide_output(server_tab, "mode"):

				actor = "<font foreground='%s'>%s</font>" % (
					color.get_nick_color(actor), actor)
				target = "<font foreground='%s'>%s</font>" % (
					color.get_nick_color(target), target)

				gui.currentServerPrint(time, server,
					"• %(actor)s set %(mode)s%(param)s on %(target)s" % {
						"actor":actor,
						"mode":mode,
						"param":param,
						"target":target},
					"action")
		else:
			# suitable channel/query found, print it there

			n_updatePrefix(tab, param, mode)

			type = "action"
			victim = target
			own = (target == server_tab.nick)

			if (param == server_tab.nick) or own:
				type = "hightlightaction"
			elif own:
				victim = "you"

			if param: param = " "+param

			if _show_output_exclusive(server_tab, tab, "mode", own = own):

				actor = "<font foreground='%s'>%s</font>" % (
					color.get_nick_color(actor), actor)
				victim = "<font foreground='%s'>%s</font>" % (
					color.get_nick_color(victim), victim)

				gui.channelPrint(time, server, tab.name,
					"• %(actor)s set %(mode)s%(param)s on %(victim)s." % {
							"actor":actor,
							"mode":mode,
							"param":param,
							"victim":victim},
					type)


def userOper_cb(time, server):
	"""
		yay, somebody gives the user oper rights.
	"""
	gui.currentServerPrint(time, server, "• You got oper access.")

def userCTCP_cb(time, server,  from_str, target, message):
	"""
		A user sends a CTCP request to target.
		I don't know a case in which target is not a channel
		and not queried.
	"""
	nick = parse_from(from_str)[0]
	server_tab = gui.tabs.search_tab(server)

	if nick.lower() == server_tab.nick.lower():
		# we wrote us
		ownCTCP_cb(time, server, target, message)

	elif target.lower() == server_tab.nick.lower():
		# someone wrote us, put in into a query
		queryCTCP_cb(time, server, from_str, message)

	else:
		# normal ctcp
		headline = _("CTCP from %(nick)s to Channel:") % {
			"nick":gui.escape(nick)}

		gui.channelPrint(time, server, target,
			"<font foreground='#00DD33'>%s</font> %s" %	(
				headline, gui.escape(message)))

def ownCTCP_cb(time, server, target, message):
	"""
		The maki user sends a CTCP request to
		a channel or user (target).
	"""
	server_tab, tab = gui.tabs.search_tabs(server, target)

	if tab:
		# valid query/channel found, print it there

		nickColor = config.get("colors","own_nick","#000000")
		textColor = config.get("colors","own_text","#000000")

		gui.channelPrint(time, server, tab.name,
			"&lt;CTCP:<font foreground='%s' weight='bold'>%s</font>&gt; "
			"<font foreground='%s'>%s</font>" % (
				nickColor,
				server_tab.nick,
				textColor,
				gui.escape(message)))

	else:
		gui.serverPrint(time, server,
			_("CTCP request from you to %(target)s: %(message)s") % {
				"target": gui.escape(target),
				"message": gui.escape(message)})

def queryCTCP_cb(time, server, from_str, message):
	"""
		A user sends us a CTCP request over a query.

		If no query window is open, send it to the server tab.
	"""
	nick = parse_from(from_str)[0]
	tab = gui.tabs.search_tab(server, nick)

	if tab:
		gui.channelPrint(time, server, tab.name, \
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s"
				"</font>&gt; <font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					gui.escape(nick),
					color.get_text_color(nick),
					gui.escape(message)))
	else:
		gui.currentServerPrint(time, server,
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s"
				"</font>&gt; <font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					gui.escape(nick),
					color.get_text_color(nick),
					gui.escape(message)))

def ownNotice_cb(time, server, target, message):
	"""
		if query channel with ``target`` exists, print
		the notice there, else print it on the current
		channel of the network which is identified by
		`server`
	"""
	server_tab, tab = gui.tabs.search_tabs(server, target)
	ownNickColor = config.get("colors","own_nick","#000000")
	ownNick = server_tab.nick

	if tab:
		gui.channelPrint(time, server, tab.name, \
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % \
				(color.get_nick_color(target), gui.escape(target),
				color.get_text_color(target), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server,
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % \
				(color.get_nick_color(target), gui.escape(target),
				color.get_text_color(target), gui.escape(message)))


def queryNotice_cb(time, server, from_str, message):
	"""
		A user sends a notice directly to the maki user.
	"""
	nick = parse_from(from_str)[0]

	tab = gui.tabs.search_tab(server, nick)
	if tab:
		if tab.name != nick:
			# correct notation of tab name
			tab.name = nick

	if tab:
		gui.channelPrint(time, server, tab.name,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % \
				(color.get_nick_color(nick), gui.escape(nick),
				color.get_text_color(nick), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % \
				(color.get_nick_color(nick), gui.escape(nick),
				color.get_text_color(nick), gui.escape(message)))

def userNotice_cb(time, server, from_str, target, message):
	"""
		A user noticed to a channel (target).
	"""
	nick = parse_from(from_str)[0]
	server_tab = gui.tabs.search_tab(server)

	if nick.lower() == server_tab.nick.lower():
		ownNotice_cb(time, server, target, message)
		return
	elif target.lower() == server_tab.nick.lower():
		queryNotice_cb(time, server, from_str, message)
		return

	gui.channelPrint(time, server, target,
			"-<font foreground='%s' weight='bold'>%s</font>- "
			"<font foreground='%s'>%s</font>" % (
				color.get_nick_color(nick),
				gui.escape(nick),
				color.get_text_color(nick),
				gui.escape(message)))

def ownAction_cb(time, server, channel, action):

	_createTab(server, channel)

	nickColor = config.get("colors","own_nick","#000000")
	textColor = config.get("colors","own_text","#000000")

	gui.channelPrint(time, server, channel,
		"<font foreground='%s' weight='bold'>%s</font> "
		"<font foreground='%s'>%s</font>" % (
			nickColor,
			gui.tabs.search_tab(server).nick,
			textColor,
			gui.escape(action)))

def actionQuery_cb(time, server, from_str, action):

	nick = parse_from(from_str)[0]

	_createTab(server, nick)

	gui.channelPrint(time, server, nick,
		"%s %s" % (nick, gui.escape(action)))

	gui.set_urgent(True)

def userAction_cb(time, server, from_str, channel, action):
	"""
		A user sent a action (text in third person)
	"""
	nick = parse_from(from_str)[0]
	server_tab = gui.tabs.search_tab(server)

	if nick.lower() == server_tab.nick.lower():
		ownAction_cb(time, server, channel, action)
		return

	elif channel.lower() == server_tab.nick.lower():
		actionQuery_cb(time, server, from_str, action)
		return

	action = gui.escape(action)

	if isHighlighted(server_tab, action):
		type = "highlightaction"
		actionString = action
		gui.set_urgent(True)
	else:
		type = "action"
		actionString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick), action)

	gui.channelPrint(time, server, channel,
		"<font foreground='%s' weight='bold'>%s</font> %s" % (
			color.get_nick_color(nick), nick, actionString), type)

def userNick_cb(time, server, from_str, newNick):
	"""
	A user (or the maki user) changed it's nick.
	If a query window for this nick on this server
	exists, it's name would be changed.
	"""
	nick = parse_from(from_str)[0]

	# find a query
	server_tab, tab = gui.tabs.search_tabs(server, nick)

	# rename query if found
	if tab and tab.is_query():
		tab.name = newNick

	own = False

	# we changed the nick
	if not nick or nick == server_tab.nick:
		message = _(u"• You are now known as %(newnick)s.")
		server_tab.nick = newNick
		own = True

	# someone else did
	else:
		message = _(u"• %(nick)s is now known as %(newnick)s.")

	# iterate over all channels and look if the nick is
	# present there. If true so rename him in nicklist cache.
	for tab in gui.tabs.get_all_tabs(servers = [server])[1:]:

		if not nick or newNick == server_tab.nick:
			# notification, print everytime
			doPrint = True
		else:
			doPrint = _show_output_exclusive(server_tab, tab, "nick", own)

		if tab.is_channel():
			if (nick in tab.nickList.get_nicks()):
				tab.nickList.modify_nick(nick, newNick)
			else:
				continue

		if tab.is_query() and tab.name != newNick:
			continue

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			color.get_nick_color(nick),
			gui.escape(nick))

		newNickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			color.get_nick_color(newNick),
			gui.escape(newNick))

		if doPrint:
			gui.channelPrint(time, server, tab.name,
				message % {
					"nick": nickString,
					"newnick": newNickString
				},
				"action")

def userKick_cb(time, server, from_str, channel, who, reason):
	"""
		signal emitted if a user got kicked.
		If the kicked user is ourself mark the channel as
		joined=False
	"""
	nick = parse_from(from_str)[0]
	server_tab, tab = gui.tabs.search_tabs(server, channel)

	if not tab:
		logging.debug("userKick: channel '%s' does not exist." % (channel))
		return

	channelString = "<font foreground='%s'>%s</font>" % (
		color.get_text_color(channel), gui.escape(channel))

	nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
		color.get_nick_color(nick), gui.escape(nick))

	reasonString = "<font foreground='%s'>%s</font>" % (
		color.get_text_color(nick), gui.escape(reason))

	if who == server_tab.nick:
		tab.joined = False

		if _show_output_exclusive(server_tab, tab, "kick", own = True):

			message = _(u"« You have been kicked from %(channel)s "
				u"by %(nick)s (%(reason)s)." % {
					"channel": channelString,
					"nick": nickString,
					"reason": reasonString })

			gui.channelPrint(time, server, channel, message,
				"highlightaction")

	else:
		tab.nickList.remove_nick(who)

		if gui.tabs.is_active(tab):
			gui.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		if _show_output_exclusive(server_tab, tab, "kick"):

			whoString = "<font foreground='%s' weight='bold'>%s</font>" % (
				color.get_nick_color(who), gui.escape(who))

			message = _(u"« %(who)s was kicked from %(channel)s by "
						u"%(nick)s (%(reason)s).") % {
				"who": whoString,
				"channel": channelString,
				"nick": nickString,
				"reason": reasonString }

			gui.channelPrint(time, server, channel, message, "action")

def userQuit_cb(time, server, from_str, reason):
	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False (as well as the
	connect-flags of the childs).

	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	server_tab = gui.tabs.search_tab(server)
	nick = parse_from(from_str)[0]

	if not server_tab:
		# tab was closed before
		return

	if nick == server_tab.nick:
		# set the connected flag to False for the server

		server_tab.connected = False

		hideServerPrint = _hide_output(server_tab, "quit", own = True)

		# walk through all channels and set joined = False on them
		channels = gui.tabs.get_all_tabs(servers = [server])[1:]

		if reason:
			message = _(u"« You have quit (%(reason)s).")
		else:
			message = _(u"« You have quit.")

		# deactivate channels/queries
		for channelTab in channels:

			hideChannelPrint = _hide_output(channelTab, "quit",
				own = True)

			if channelTab.is_channel():
				channelTab.joined = False

			channelTab.connected = False

			if not (hideServerPrint or hideChannelPrint):
				gui.channelPrint(time, server, channelTab.name,
					message % {"reason": reason}, "action")

	else: # another user quit the network

		hideServerPrint = _hide_output(server_tab, "quit")

		if reason:
			message = _(u"« %(nick)s has quit (%(reason)s).")
		else:
			message = _(u"« %(nick)s has quit.")

		nickString = "<font foreground='%s' weight='bold'>"\
			"%s</font>" % (
				color.get_nick_color(nick),
				gui.escape(nick))

		reasonString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick),
			gui.escape(reason))

		message = message % {
			"nick": nickString,
			"reason": reasonString}

		channels = gui.tabs.get_all_tabs(servers = [server])[1:]

		if not channels:
			logging.debug("No channels but quit reported.. Hum wtf? o.0")
			return

		# print in all channels where nick joined a message
		for channelTab in channels:

			hideChannelPrint = _hide_output(channelTab, "quit")

			if channelTab.is_query():
				# on query with `nick` only print quitmessage

				if (not (hideChannelPrint or hideServerPrint)
				and channelTab.name.lower() == nick.lower()):
					gui.channelPrint(time, server, channelTab.name,
						message, "action")

				# skip nickList modification for queries
				continue

			# search for the nick in the channel
			# and print the quit message if the
			# nick was found.
			nickList = channelTab.nickList
			nicks = nickList.get_nicks() or []

			if nick in nicks:
				nickList.remove_nick(nick)

				if gui.tabs.is_active(channelTab):
					# update gui display for usercount
					gui.set_user_count(len(nickList),
						nickList.get_operator_count())

				if not (hideServerPrint or hideChannelPrint):
					gui.channelPrint(time, server, channelTab.name,
						message, "action")


def userJoin_cb(timestamp, server, from_str, channel):
	"""
	A user identified by "nick" joins the channel "channel" on
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	nick = parse_from(from_str)[0]
	stab, tab = gui.tabs.search_tabs(server, channel)
	doPrint = False

	if nick == stab.nick:
		# we joined a channel, fetch nicks and topic, create
		# channel and print the log

		if not tab:
			tab = gui.tabs.create_channel(stab, channel)

			if not gui.tabs.add_tab(stab, tab):
				raise Exception, \
					"userJoin_cb: adding tab for channel '%s' failed." % (
					channel)

			gui.print_last_log(server, channel)

		tab.nickList.clear()

		if gui.tabs.is_active(tab):
			gui.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		tab.joined = True
		tab.connected = True

		if config.get_bool("tekka","switch_to_channel_after_join"):
			gui.tabs.switch_to_path(tab.path)

		doPrint = _show_output_exclusive(stab, tab, "join", own = True)

		if doPrint:

			nickString = "You"
			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel), gui.escape(channel))

			message = _(u"» You have joined %(channel)s.")

	else: # another one joined the channel

		if not tab:
			raise Exception, \
				"No tab for channel '%s' in userJoin (not me)."

		doPrint = _show_output_exclusive(stab, tab, "join", own = False)

		if doPrint:
			message = _(u"» %(nick)s has joined %(channel)s.")

			nickString = "<font foreground='%s' weight='bold'>"\
				"%s</font>" % (
					color.get_nick_color(nick),
					gui.escape(nick))

			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel),
				gui.escape(channel))


		tab.nickList.append_nick(nick)

		if gui.tabs.is_active(tab):
			gui.set_user_count(len(tab.nickList),
				tab.nickList.get_operator_count())

	if doPrint:
		message = message % {
			"nick": nickString,
			"channel": channelString }

		gui.channelPrint(timestamp, server, channel, message, "action")

def userNames_cb(timestamp, server, channel, nicks, prefixes):
	"""
	this signal is called for each nick in the channel.
	remove the nick to make sure it isn't there (hac--workaround),
	add the nick, fetch the prefix for it and at least
	update the user count.

	To avoid a non existent channel this method checks against
	a missing channel tab and adds it if needed.
	"""
	tab = gui.tabs.search_tab(server, channel)

	if not tab:
		serverTab = gui.tabs.search_tab(server)
		tab = gui.tabs.create_channel(serverTab, channel)

		if not gui.tabs.add_tab(serverTab, tab):
			raise Exception, "adding tab for channel '%s' failed." % (
				channel)

		gui.print_last_log(server, channel)

		tab.joined = True
		tab.connected = True

	if not nicks:
		# end of list
		tab.nickList.sort_nicks()

	else:
		for i in xrange(len(nicks)):
			# FIXME
			tab.nickList.remove_nick(nicks[i])
			tab.nickList.append_nick(nicks[i], sort=False)

			if prefixes[i]:
				tab.nickList.set_prefix(nicks[i], prefixes[i], sort=False)

		if gui.tabs.is_active(tab):
			gui.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())


def userPart_cb(timestamp, server, from_str, channel, reason):
	"""
	A user parted the channel.

	If we are the user who parted, mark the channel
	as parted (joined=False)
	"""
	nick = parse_from(from_str)[0]

	stab, tab = gui.tabs.search_tabs(server, channel)

	if not tab:
		# tab was closed
		return

	if nick == stab.nick:
		# we parted

		tab.joined = False

		if _show_output_exclusive(stab, tab, "part", own = True):

			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel), gui.escape(channel))

			reasonString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(nick), gui.escape(reason))

			if reason:
				message = _(u"« You have left %(channel)s (%(reason)s).")
			else:
				message = _(u"« You have left %(channel)s.")

			gui.channelPrint(timestamp, server, channel,
				message % {
					"channel": channelString,
					"reason": reasonString },
				"action")

	else: # another user parted

		tab.nickList.remove_nick(nick)

		if gui.tabs.is_active(tab):
			gui.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		if _show_output_exclusive(stab, tab, "part", False):

			nickString = "<font foreground='%s' weight='bold'>"\
				"%s</font>" % (
				color.get_nick_color(nick), gui.escape(nick))

			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel), gui.escape(channel))

			reasonString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(nick), gui.escape(reason))

			if reason:
				message = _(u"« %(nick)s has left %(channel)s "\
					"(%(reason)s).")
			else:
				message = _(u"« %(nick)s has left %(channel)s.")

			gui.channelPrint(timestamp, server, channel,
				message % {
					"nick": nickString,
					"channel": channelString,
					"reason": reasonString
					},
				"action")

def userError_cb(time, server, domain, reason, arguments):
	if domain == "no_such":
		noSuch(time, server, arguments[0], reason)

	elif domain == "cannot_join":
		cannotJoin(time, server, arguments[0], reason)

def noSuch(time, server, target, type):
	""" Signal is emitted if maki can't find the target on the server. """

	tab = gui.tabs.search_tab(server, target)

	if type == "nick":
		error = _(u"• %(target)s: No such nick/channel.") % {
			"target": gui.escape(target) }
	elif type == "server":
		error = _(u"• %(target)s: No such server.") % {
			"target": gui.escape(target) }
	elif type == "channel":
		error = _(u"• %(target)s: No such channel.") % {
			"target": gui.escape(target) }

	if tab:
		gui.channelPrint(time, server, target, error)
	else:
		gui.serverPrint(time, server, error)

def cannotJoin(time, server, channel, reason):
	""" The channel could not be joined.
		reason : { l (full), i (invite only), b (banned), k (key) }
	"""
	message = _("Unknown reason")

	if reason == "full":
		message = _("The channel is full.")
	elif reason == "invite":
		message = _("The channel is invite-only.")
	elif reason == "banned":
		message = _("You are banned.")
	elif reason == "key":
		if config.get_bool("tekka", "ask_for_key_on_cannotjoin"):

			def key_dialog_response_cb(dialog, id):
				if id == gtk.RESPONSE_OK:
					sushi.join(server, channel, dialog.entry.get_text())
				dialog.destroy()

			# open a input dialog which asks for the key
			d = key_dialog.KeyDialog(server, channel)
			d.connect("response", key_dialog_response_cb)
			gui.showInlineDialog(d)
			return

		else:
			message = _("You need the correct channel key.")

	gui.currentServerPrint (time, server,
		_("You can not join %(channel)s: %(reason)s" % {
			"channel":channel,
			"reason":message
			}
		))

def channelList_cb(time, server, channel, users, topic):
	""" Signal for /list command.
		Prints content of the listing.
	"""

	def init_channelList():
		channelList_cb._text = []
		channelList_cb._line = 0

		serverTab = gui.tabs.search_tab(server)
		channelList_cb._buf = serverTab.window.textview.get_buffer()

	def print_listing(buf, text):
		buf.insertHTML(buf.get_end_iter(), "<br/>".join(text))
		return False

	try:
		channelList_cb._init
	except AttributeError:
		channelList_cb._init = 0

	if not channelList_cb._init:
		init_channelList()
		channelList_cb._init = 1

	if not channel and not topic and users == -1:
		# listing ended, reset variables

		if channelList_cb._line > 0:
			# print rest
			gobject.idle_add(print_listing, channelList_cb._buf,
				channelList_cb._text)

		gobject.idle_add(gui.serverPrint, time, server, "End of list.")

		init_channelList()
		channelList_cb._init = 0

	else:
		channelList_cb._text.append(("• <b>%s</b><br/>"+
			"\t%d "+_("User")+"<br/>"+
			"\t"+_("Topic")+": \"%s\"") % \
			(gui.escape(channel), users, gui.escape(topic)))

		channelList_cb._line += 1

		if channelList_cb._line == 10:
			gobject.idle_add(print_listing, channelList_cb._buf,
				channelList_cb._text)

			channelList_cb._text = []
			channelList_cb._line = 0

def whois_cb(time, server, nick, message):
	""" message = "" => end of whois """
	if message:
		gui.serverPrint(time, server,
			_(u"[%(nick)s] %(message)s") % {
				"nick": gui.escape(nick),
				"message": gui.escape(message) })
	else:
		gui.serverPrint(time, server,
			_(u"[%(nick)s] End of whois.") % {
				"nick": gui.escape(nick) })

def dcc_send_cb(time, id, server, sender, filename,
			 size, progress, speed, status):
	"""
	status:
	- 1 << 0 = incoming
	- 1 << 1 = resumed
	- 1 << 2 = running
	- 1 << 3 = error

	"" in (server, sender, filename)
		and 0 in (size, progress, speed, status):
	send was removed
	"""

	def dcc_dialog_response_cb(dialog, id, tid):
		if id == gtk.RESPONSE_OK:
			sushi.dcc_send_accept(tid)
		elif id == gtk.RESPONSE_CANCEL:
			sushi.dcc_send_remove(tid)
		dialog.destroy()

	(s_new,
	 s_incoming,
	 s_resumable,
	 s_resumed,
	 s_running,
	 s_error) = [1 << n for n in range(6)]

	if (server == "" and sender == "" and filename == ""
	and size == 0 and progress == 0 and speed == 0 and status == 0):

		# send was removed
		logging.debug("filetransfer %d removed." % (id))
		return

	logging.debug("status is %d." % (status))

	# handle incoming transfers
	#
	if status & s_incoming == s_incoming:

		if status & s_new == s_new:
			# attempt made

			d = dcc_dialog.DCCDialog(
				id, parse_from(sender)[0],
				filename, size,
				resumable = (status & s_resumable == s_resumable))

			d.connect("response", dcc_dialog_response_cb, id)
			gui.showInlineDialog(d)
