# coding:UTF-8
"""
Copyright (c) 2009-2010 Marian Tietz
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

import gtk
import gobject
import logging
import string
import time as mtime

from dbus import UInt64
from gettext import gettext as _

from tekka import com
from tekka import config
from tekka import signals
from tekka import gui

from tekka.lib import contrast

from tekka.com import sushi, parse_from
from tekka.signals import connect_signal
from tekka.lib import key_dialog
from tekka.lib import dcc_dialog
from tekka.lib import inline_dialog

from tekka.helper import code
from tekka.helper import color
from tekka.helper import markup
from tekka.typecheck import types

init = False


def setup():
	sushi.g_connect("maki-connected", maki_connected_cb)
	sushi.g_connect("maki-disconnected", maki_disconnected_cb)


def maki_connected_cb(sushi):
	global init

	if init == False:
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

		init = True

	_add_servers()


def maki_disconnected_cb(sushi):
	pass


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

		if tab.is_active():
			gui.set_topic(markup.markup_escape(tab.topic))
			gui.mgmt.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		# TODO: handle topic setter
		tab.joined = True
		tab.connected = True

		if add:
			gui.tabs.add_tab(server_tab, tab, update_shortcuts = False)
			tab.print_last_log()

		topic = sushi.channel_topic(server_tab.name, channel)
		_report_topic(mtime.time(), server_tab.name, channel, topic)

	gui.shortcuts.assign_numeric_tab_shortcuts(gui.tabs.get_all_tabs())

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
		tab.print_last_log()

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

@types (tab = gui.tabs.TekkaTab, what = basestring, own = bool)
def _hide_output(tab, what, own = False):
	""" Returns bool.
		Check if the message type determined by "what"
		shall be hidden or not.
		tab should be a TekkaServer, -Channel or -Query
	"""
	if type(tab) == gui.tabs.TekkaChannel:
		cat = "channel_%s_%s" % (
					tab.server.name.lower(),
					tab.name.lower())
	elif type(tab) == gui.tabs.TekkaQuery:
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

@types (servertab = gui.tabs.TekkaServer, tab = gui.tabs.TekkaTab,
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
	gui.mgmt.set_useable(True)

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

	tab.write(time, "Connecting...")

	gui.status.set_visible("connecting", "Connecting to %s" % server)

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

	tab.write(time, "Connected.")

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
			tab.update()

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
		first_time[server].write(time, markup.escape(message),
			no_general_output = True)

""" Callbacks for channel interaction """

def _report_topic(time, server, channel, topic):
	message = _(u"• Topic for %(channel)s: %(topic)s") % {
		"channel": channel,
		"topic": markup.escape(topic) }

	tab = gui.tabs.search_tab(server, channel)

	if not tab:
		raise Exception, "%s:%s not found." % (server, channel)

	tab.write(time, message, "action", no_general_output = True)

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
		gui.mgmt.set_topic(markup.markup_escape(topic))

	if not nick:
		# just reporting the topic.
		_report_topic(time, server, channel, topic)

	else:
		if nick == serverTab.nick:
			message = _(u"• You changed the topic to %(topic)s.")
		else:
			message = _(u"• %(nick)s changed the topic to %(topic)s.")

		channelTab.write(time, message % {
								"nick": nick,
								"topic": markup.escape(topic) },
						"action")

def channelBanlist_cb(time, server, channel, mask, who, when):
	"""
		ban list signal.
	"""
	self = code.init_function_attrs(channelBanlist_cb,
		tab = gui.tabs.search_tab(server, channel))

	if not mask and not who and when == -1:
		self.tab.write(time, "End of banlist.", "action")
		code.reset_function_attrs(channelBanlist_cb)

	else:
		timestring = mtime.strftime(
			"%Y-%m-%d %H:%M:%S",
			mtime.localtime(when))

		self.tab.write(
			time,
			"%s by %s on %s" % (
				markup.escape(mask),
				markup.escape(who),
				markup.escape(timestring)),
			"action")

""" Callbacks of maki signals """

def makiShutdown_cb(time):
	gui.mgmt.myPrint("Maki is shut down!")
	gui.mgmt.set_useable(False)

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
		tab.write(
			timestamp,
			_(u"• %(nick)s is away (%(message)s).") % {
				"nick": nick,
				"message": markup.escape(message)},
			"action")

		if tab and tab.name == nick:
			tab.printed_away_message = True


def userMessage_cb(timestamp, server, from_str, channel, message):
	"""
		PRIVMSGs are coming in here.
	"""
	nick = parse_from(from_str)[0]
	(server_tab, channel_tab) = gui.tabs.search_tabs(server, channel)

	if nick.lower() == server_tab.nick.lower():
		ownMessage_cb(timestamp, server, channel, message)
		return

	elif channel.lower() == server_tab.nick.lower():
		userQuery_cb(timestamp, server, from_str, message)
		return

	message = markup.escape(message)

	if isHighlighted(server_tab, message):
		# set mode to highlight and disable setting
		# of text color for the main message (would
		# override channelPrint() highlight color)

		type = "highlightmessage"
		messageString = message
		gui.mgmt.set_urgent(True)
	else:
		# no highlight, normal message type and
		# text color is allowed.

		type = "message"
		messageString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick), message)

	channel_tab.write(timestamp,
		"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			_getPrefix(server, channel, nick),
			color.get_nick_color(nick),
			markup.escape(nick),
			messageString,
		), type)


def ownMessage_cb(timestamp, server, channel, message):
	"""
		The maki user wrote something on a channel or a query
	"""
	tab = _createTab(server, channel)
	nick = gui.tabs.search_tab(server).nick

	tab.write(timestamp,
			"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt;"
			" <font foreground='%s'>%s</font>" % (
				_getPrefix(server, channel, nick),
				config.get("colors","own_nick","#000000"),
				nick,
				config.get("colors","own_text","#000000"),
				markup.escape(message)))


def userQuery_cb(timestamp, server, from_str, message):
	"""
		A user writes to us in a query.
	"""
	nick = parse_from(from_str)[0]

	tab = _createTab(server, nick)

	tab.write(timestamp,
		"&lt;<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			color.get_nick_color(nick),
			markup.escape(nick),
			markup.escape(message)
		), "message")

	# queries are important
	gui.mgmt.set_urgent(True)


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

			if tab.is_active():
				gui.mgmt.set_user_count(len(tab.nickList),
					tab.nickList.get_operator_count())

	nick = parse_from(from_str)[0]

	# nick: /mode target +mode param
	server_tab = gui.tabs.search_tab(server)

	if not nick:
		# only a mode listing
		server_tab.current_write(
			time,
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

				server_tab.current_write(
					time,
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

				tab.write(time,
					"• %(actor)s set %(mode)s%(param)s on %(victim)s." % {
						"actor": actor,
						"mode": mode,
						"param": param,
						"victim": victim},
					type)


def userOper_cb(time, server):
	"""
		yay, somebody gives the user oper rights.
	"""
	server_tab = gui.tabs.search_tab(server)
	server_tab.current_write(time, "• You got oper access.")


def userCTCP_cb(time, server,  from_str, target, message):
	"""
		A user sends a CTCP request to target.
		I don't know a case in which target is not a channel
		and not queried.
	"""
	nick = parse_from(from_str)[0]
	(server_tab, target_tab) = gui.tabs.search_tabs(server, target)

	if nick.lower() == server_tab.nick.lower():
		# we wrote us
		ownCTCP_cb(time, server, target, message)

	elif target.lower() == server_tab.nick.lower():
		# someone wrote us, put in into a query
		queryCTCP_cb(time, server, from_str, message)

	else:
		# normal ctcp
		headline = _("CTCP from %(nick)s to Channel:") % {
			"nick": markup.escape(nick)}

		target_tab.write(time,
			"<font foreground='#00DD33'>%s</font> %s" %	(
				headline, markup.escape(message)))


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

		tab.write(time,
			"&lt;CTCP:<font foreground='%s' weight='bold'>%s</font>&gt; "
			"<font foreground='%s'>%s</font>" % (
				nickColor,
				server_tab.nick,
				textColor,
				markup.escape(message)))

	else:
		server_tab.write(time,
			_("CTCP request from you to %(target)s: %(message)s") % {
				"target": markup.escape(target),
				"message": markup.escape(message)})

def queryCTCP_cb(time, server, from_str, message):
	"""
		A user sends us a CTCP request over a query.

		If no query window is open, send it to the server tab.
	"""
	nick = parse_from(from_str)[0]
	(server_tab, tab) = gui.tabs.search_tabs(server, nick)

	if tab:
		tab.write(time,
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s"
				"</font>&gt; <font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					markup.escape(nick),
					color.get_text_color(nick),
					markup.escape(message)))
	else:
		server_tab.current_write(time,
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s"
				"</font>&gt; <font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					markup.escape(nick),
					color.get_text_color(nick),
					markup.escape(message)))

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
		tab.write(time,
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % (
				color.get_nick_color(target),
				markup.escape(target),
				color.get_text_color(target),
				markup.escape(message)))
	else:
		server_tab.current_write(time,
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % (
				color.get_nick_color(target),
				markup.escape(target),
				color.get_text_color(target),
				markup.escape(message)))


def queryNotice_cb(time, server, from_str, message):
	"""
		A user sends a notice directly to the maki user.
	"""
	nick = parse_from(from_str)[0]

	(server_tab, tab) = gui.tabs.search_tabs(server, nick)

	if tab:
		if tab.name != nick:
			# correct notation of tab name
			tab.name = nick

	if tab:
		tab.write(time,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					markup.escape(nick),
					color.get_text_color(nick),
					markup.escape(message)))
	else:
		server_tab.current_write(time,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % (
					color.get_nick_color(nick),
					markup.escape(nick),
					color.get_text_color(nick),
					markup.escape(message)))


def userNotice_cb(time, server, from_str, target, message):
	""" An incoming notice """
	nick = parse_from(from_str)[0]
	(server_tab, target_tab) = gui.tabs.search_tabs(server, target)

	if nick.lower() == server_tab.nick.lower():
		# we wrote that notice
		ownNotice_cb(time, server, target, message)
		return

	elif target.lower() == server_tab.nick.lower():
		# it's supposed to be a private (query) message
		queryNotice_cb(time, server, from_str, message)
		return

	message = "-<font foreground='%s' weight='bold'>%s</font>- "\
			  "<font foreground='%s'>%s</font>" % (
				color.get_nick_color(nick),
				markup.escape(nick),
				color.get_text_color(nick),
				markup.escape(message))

	if target_tab == None:
		# global notice
		server_tab.current_write(time, message)
	else:
		# channel/query notice
		target_tab.write(time, message)


def ownAction_cb(time, server, channel, action):

	tab = _createTab(server, channel)

	nickColor = config.get("colors","own_nick","#000000")
	textColor = config.get("colors","own_text","#000000")

	tab.write(time,
		"<font foreground='%s' weight='bold'>%s</font> "
		"<font foreground='%s'>%s</font>" % (
			nickColor,
			gui.tabs.search_tab(server).nick,
			textColor,
			markup.escape(action)))


def actionQuery_cb(time, server, from_str, action):
	""" action in a query """

	nick = parse_from(from_str)[0]

	tab = _createTab(server, nick)

	tab.write(time, "%s %s" % (nick, markup.escape(action)))

	gui.mgmt.set_urgent(True)


def userAction_cb(time, server, from_str, channel, action):
	""" normal action """

	nick = parse_from(from_str)[0]
	(server_tab, channel_tab) = gui.tabs.search_tabs(server, channel)

	if nick.lower() == server_tab.nick.lower():
		ownAction_cb(time, server, channel, action)
		return

	elif channel.lower() == server_tab.nick.lower():
		actionQuery_cb(time, server, from_str, action)
		return

	action = markup.escape(action)

	if isHighlighted(server_tab, action):
		type = "highlightaction"
		actionString = action
		gui.mgmt.set_urgent(True)

	else:
		type = "action"
		actionString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick), action)

	channel_tab.write(
			time,
			"<font foreground='%s' weight='bold'>%s</font> %s" % (
				color.get_nick_color(nick),
				nick,
				actionString),
			type)


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
			# ignore not associated queries
			continue

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			color.get_nick_color(nick),
			markup.escape(nick))

		newNickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			color.get_nick_color(newNick),
			markup.escape(newNick))

		if doPrint:
			tab.write(time,
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
		color.get_text_color(channel), markup.escape(channel))

	nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
		color.get_nick_color(nick), markup.escape(nick))

	reasonString = "<font foreground='%s'>%s</font>" % (
		color.get_text_color(nick), markup.escape(reason))

	if who == server_tab.nick:
		tab.joined = False

		if _show_output_exclusive(server_tab, tab, "kick", own = True):

			message = _(u"« You have been kicked from %(channel)s "
				u"by %(nick)s (%(reason)s)." % {
					"channel": channelString,
					"nick": nickString,
					"reason": reasonString })

			tab.write(time, message, "highlightaction")

	else:
		tab.nickList.remove_nick(who)

		if tab.is_active():
			gui.mgmt.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		if _show_output_exclusive(server_tab, tab, "kick"):

			whoString = "<font foreground='%s' weight='bold'>%s</font>" % (
				color.get_nick_color(who), markup.escape(who))

			message = _(u"« %(who)s was kicked from %(channel)s by "
						u"%(nick)s (%(reason)s).") % {
				"who": whoString,
				"channel": channelString,
				"nick": nickString,
				"reason": reasonString }

			tab.write(time, message, "action")

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
				channelTab.write(time, message % {
									"reason": reason},
								"action")

	else: # another user quit the network

		hideServerPrint = _hide_output(server_tab, "quit")

		if reason:
			message = _(u"« %(nick)s has quit (%(reason)s).")
		else:
			message = _(u"« %(nick)s has quit.")

		nickString = "<font foreground='%s' weight='bold'>"\
			"%s</font>" % (
				color.get_nick_color(nick),
				markup.escape(nick))

		reasonString = "<font foreground='%s'>%s</font>" % (
			color.get_text_color(nick),
			markup.escape(reason))

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
					channelTab.write(time, message, "action")

				# skip nickList modification for queries
				continue

			# search for the nick in the channel
			# and print the quit message if the
			# nick was found.
			nickList = channelTab.nickList
			nicks = nickList.get_nicks() or []

			if nick in nicks:
				nickList.remove_nick(nick)

				if channelTab.is_active():
					# update gui display for usercount
					gui.mgmt.set_user_count(len(nickList),
						nickList.get_operator_count())

				if not (hideServerPrint or hideChannelPrint):
					channelTab.write(time, message, "action")


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

			tab.print_last_log()

		tab.nickList.clear()

		if tab.is_active():
			gui.mgmt.set_user_count(
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
				color.get_text_color(channel), markup.escape(channel))

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
					markup.escape(nick))

			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel),
				markup.escape(channel))


		tab.nickList.append_nick(nick)

		if tab.is_active():
			gui.mgmt.set_user_count(len(tab.nickList),
				tab.nickList.get_operator_count())

	if doPrint:
		message = message % {
			"nick": nickString,
			"channel": channelString }

		tab.write(timestamp, message, "action")

def userNames_cb(timestamp, server, channel, nicks, prefixes):
	"""
	this signal is called for each nick in the channel.
	remove the nick to make sure it isn't there (hac--workaround),
	add the nick, fetch the prefix for it and at least
	update the user count.
	"""
	tab = gui.tabs.search_tab(server, channel)

	if not tab: # /names for unexisting channel?
		return

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

		if tab.is_active():
			gui.mgmt.set_user_count(
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
				color.get_text_color(channel), markup.escape(channel))

			reasonString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(nick), markup.escape(reason))

			if reason:
				message = _(u"« You have left %(channel)s (%(reason)s).")
			else:
				message = _(u"« You have left %(channel)s.")

			tab.write(timestamp,
						message % {
							"channel": channelString,
							"reason": reasonString },
						"action")

	else: # another user parted

		tab.nickList.remove_nick(nick)

		if tab.is_active():
			gui.mgmt.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

		if _show_output_exclusive(stab, tab, "part", False):

			nickString = "<font foreground='%s' weight='bold'>"\
				"%s</font>" % (
				color.get_nick_color(nick), markup.escape(nick))

			channelString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(channel), markup.escape(channel))

			reasonString = "<font foreground='%s'>%s</font>" % (
				color.get_text_color(nick), markup.escape(reason))

			if reason:
				message = _(u"« %(nick)s has left %(channel)s "\
					"(%(reason)s).")
			else:
				message = _(u"« %(nick)s has left %(channel)s.")

			tab.write(timestamp,
						message % {
							"nick": nickString,
							"channel": channelString,
							"reason": reasonString},
						"action")


def userError_cb(time, server, domain, reason, arguments):
	if domain == "no_such":
		noSuch(time, server, arguments[0], reason)

	elif domain == "cannot_join":
		cannotJoin(time, server, arguments[0], reason)

	elif domain == "privilege":
		if reason == "channel_operator":
			tab = gui.tabs.search_tab(server, arguments[0])

			message = _(u"• You are not a channel operator.")
			tab.write(time, message)


def noSuch(time, server, target, type):
	""" Signal is emitted if maki can't find the target on the server. """

	(server_tab, tab) = gui.tabs.search_tabs(server, target)

	if type == "nick":
		error = _(u"• %(target)s: No such nick/channel.") % {
			"target": markup.escape(target) }
	elif type == "server":
		error = _(u"• %(target)s: No such server.") % {
			"target": markup.escape(target) }
	elif type == "channel":
		error = _(u"• %(target)s: No such channel.") % {
			"target": markup.escape(target) }

	if tab:
		tab.write(time, error)
	else:
		server_tab.write(time, error)

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
			gui.mgmt.show_inline_dialog(d)
			return

		else:
			message = _("You need the correct channel key.")

	server_tab = gui.tabs.search_tab(server)

	server_tab.current_write(time,
		_("You can not join %(channel)s: %(reason)s" % {
			"channel":channel,
			"reason":message
			}))


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


	# create dcc_news new-transfer-cache
	self = code.init_function_attrs(dcc_send_cb,
		dcc_news={},
		dcc_notifies={})

	if (server == "" and sender == "" and filename == ""
	and size == 0 and progress == 0 and speed == 0 and status == 0):

		# send was removed
		logging.debug("filetransfer %d removed." % (id))

		try:
			del self.dcc_news[id]
			del self.dcc_notifies[id]
		except KeyError:
			pass

		return

	logging.debug("status is %d." % (status))

	# import dcc transfer states
	from tekka.helper.dcc import s_new, s_incoming, s_resumable, s_running

	# handle incoming transfer
	if status & s_incoming == s_incoming:

		if status & s_new == s_new:
			# attempt made

			d = dcc_dialog.DCCDialog(
				id, parse_from(sender)[0],
				filename, size,
				resumable = (status & s_resumable == s_resumable))

			self.dcc_news[id] = True

			d.connect("response", dcc_dialog_response_cb, id)
			gui.mgmt.show_inline_dialog(d)

		elif status & s_running and status & s_incoming:
			if not self.dcc_news.has_key(id) and not self.dcc_notifies.has_key(id):
				# notify about auto accepted file transfer
				d = inline_dialog.InlineMessageDialog(
					_("Auto accepted file transfer"),
					_("maki auto accepted the following file transfer:\n"
					  "Filename: %(filename)s\n"
					  "Sender: %(sender)s\n"
					  "Size: %(size)s\n"
					  "Server: %(server)s" % {
						  "filename":filename,
						  "sender":parse_from(sender)[0],
						  "size":size,
						  "server":server}),
					icon=gtk.STOCK_DIALOG_INFO)

				d.connect("response", lambda d,i: d.destroy())
				gui.mgmt.show_inline_dialog(d)

				self.dcc_notifies[id] = True
