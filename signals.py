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
from dbus import UInt64
import time as mtime

import com
import config
import gui_control as gui
from helper import keyDialog
from lib import contrast

sushi = None

signals = {}

def get_contrast_colors ():
	return (
		contrast.CONTRAST_COLOR_AQUA,
		contrast.CONTRAST_COLOR_BLACK,
		contrast.CONTRAST_COLOR_BLUE,
		contrast.CONTRAST_COLOR_BROWN,
		contrast.CONTRAST_COLOR_CYAN,
		contrast.CONTRAST_COLOR_DARK_BLUE,
		contrast.CONTRAST_COLOR_DARK_GREEN,
		contrast.CONTRAST_COLOR_DARK_GREY,
		contrast.CONTRAST_COLOR_DARK_RED,
		contrast.CONTRAST_COLOR_GREEN,
		contrast.CONTRAST_COLOR_GREY,
		contrast.CONTRAST_COLOR_LIGHT_BLUE,
		contrast.CONTRAST_COLOR_LIGHT_BROWN,
		contrast.CONTRAST_COLOR_LIGHT_GREEN,
		contrast.CONTRAST_COLOR_LIGHT_GREY,
		contrast.CONTRAST_COLOR_LIGHT_RED,
		contrast.CONTRAST_COLOR_MAGENTA,
		contrast.CONTRAST_COLOR_ORANGE,
		contrast.CONTRAST_COLOR_PURPLE,
		contrast.CONTRAST_COLOR_RED,
		contrast.CONTRAST_COLOR_VIOLET,
		contrast.CONTRAST_COLOR_WHITE,
		contrast.CONTRAST_COLOR_YELLOW
	)

def parse_from (from_str):
	h = from_str.split("!", 2)

	if len(h) < 2:
		return (h[0],)

	t = h[1].split("@", 2)

	if len(t) < 2:
		return (h[0],)

	return (h[0], t[0], t[1])

def connect_signal (signal, handler):
	""" connect handler to signal """
	global signals
	if type(signal) != type(""):
		raise TypeError

	if not signals.has_key (signal):
	  	signals[signal] = {}

	if signals[signal].has_key(handler):
		# no doubles
		return

	signals[signal][handler] = sushi.connect_to_signal (signal, handler)

def disconnect_signal (signal, handler):
	""" disconnect handler from signal """
	global signals
	if type(signal) != type(""):
		raise TypeError

	try:
		ob = signals[signal][handler]
	except KeyError:
		return
	else:
		ob.remove()
		del signals[signal][handler]

def handle_maki_disconnect():
	global sushi, signals

	sushi = None

	for signal in signals:
		for handler in signals[signal]:
			signals[signal][handler].remove()

	signals = {}

def handle_maki_connect():
	global sushi

	sushi = com.sushi

	# Message-Signals
	connect_signal("message", userMessage)
	connect_signal("notice", userNotice)
	connect_signal("action", userAction)
	connect_signal("away_message", userAwayMessage)
	connect_signal("ctcp", userCTCP)
	connect_signal("no_such", noSuch)
	connect_signal("cannot_join", cannotJoin)

	# action signals
	connect_signal("part", userPart)
	connect_signal("join", userJoin)
	connect_signal("names", userNames)
	connect_signal("quit", userQuit)
	connect_signal("kick", userKick)
	connect_signal("nick", userNick)
	connect_signal("away", userAway)
	connect_signal("back", userBack)
	connect_signal("mode", userMode)
	connect_signal("oper", userOper)

	# Server-Signals
	connect_signal("connect", serverConnect)
	connect_signal("connected", serverConnected)
	connect_signal("motd", serverMOTD)
	connect_signal("list", list)
	connect_signal("whois", whois)

	# Channel-Signals
	connect_signal("topic", channelTopic)
	connect_signal("banlist", channelBanlist)

	# Maki signals
	connect_signal("shutdown", makiShutdownSignal)

	initServers()

def initServers():
	"""
		Adds all servers to tekka which are reported by maki.
	"""
	# in case we're reconnecting, clear all stuff
	gui.widgets.get_widget("serverTree").get_model().clear()

	for server in com.fetchServers():

		sushi.nick(server, "")

		tab = gui.tabs.createServer(server)
		tab.connected = True

		# FIXME
		if com.isAway(server, com.getOwnNick(server)):
			tab.away = "OHAI"

		gui.tabs.addTab(None, tab)

		addChannels(server)

	try:
		toSwitch = gui.tabs.getAllTabs()[1]
	except IndexError:
		return
	else:
		gui.tabs.switchToPath(toSwitch.path)

def addChannels(server):
	"""
		Adds all channels to tekka wich are reported by maki.
	"""
	channels = com.fetchChannels(server)

	for channel in channels:

		add = False
		nicks, prefixes = com.fetchNicks(server, channel)

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			tab = gui.tabs.createChannel(server, channel)
			add = True

		tab.nickList.clear()
		tab.nickList.addNicks(nicks, prefixes)

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

		# TODO: handle topic setter
		tab.joined=True
		tab.connected=True

		if add:
			gui.tabs.addTab(server, tab, update_shortcuts=False)
			lastLog(server, channel)

		sushi.topic(server, channel, "")

	gui.updateServerTreeShortcuts()


def lastLog(server, channel, lines=0):
	"""
		Fetch lines amount of history text for channel
		on server.
	"""
	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		return

	buffer = tab.textview.get_buffer()

	if not buffer:
		print "lastLog('%s','%s'): no buffer" % (server,channel)
		return

	for line in com.fetchLog(
				server,
				channel,
				UInt64(lines or config.get(
					"chatting", "last_log_lines", default="0"))
				):
		buffer.insertHTML(buffer.get_end_iter(),
			"<font foreground='%s'>%s</font>" % (
				config.get("colors","last_log","#DDDDDD"),
				gui.escape(line)))

def updatePrefix(tab, nick, mode):
	"""
	checks if the mode is a prefix-mode (e.g. +o)
	If so, the prefix of the nick `nick` in channel `channel`
	will be updated (fetched).
	"""
	if not nick:
		return

	# FIXME: cache support_prefix()!
	if mode[1] in sushi.support_prefix(tab.server)[0]:
		tab.nickList.setPrefix(nick,
			com.fetchPrefix(tab.server, tab.name, nick))

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList),
				tab.nickList.get_operator_count())


def getNickColor(nick):
	"""
		Returns a static color for the nick given.
		The returned color depends on the color mapping
		set in config module.
	"""
	if not config.get_bool("tekka","color_text"):
		return

	bg_color = gui.widgets.get_widget("output").get_style().bg[gtk.STATE_NORMAL]
	print bg_color


	# FIXME
	colors = config.get_list("colors", "nick_colors")
	if not colors:
		return config.get("colors","nick","#000000")
	return colors[sum([ord(n) for n in nick]) % len(colors)]

	colors = get_contrast_colors()

	if not colors:
		return config.get("colors","nick","#000000")

	bg_color = gui.widgets.get_widget("output").get_style().bg[gtk.STATE_NORMAL]
	color = colors[sum([ord(n) for n in nick]) % len(colors)]

	return contrast.contrast_render_foreground_color(bg_color, color)

def getTextColor(nick):
	"""
		Same as getNickColor but for text and defaults
		to another value (text_message)
	"""
	if not config.get_bool("tekka","color_text"):
		return

	# FIXME
	colors = config.get_list("colors", "nick_colors")
	if not colors or not config.get_bool("tekka","color_nick_text"):
		return config.get("colors","text_message","#000000")
	return colors[sum([ord(n) for n in nick]) % len(colors)]

	colors = get_contrast_colors()

	if not colors or not config.get_bool("tekka","color_nick_text"):
		return config.get("colors","text_message","#000000")

	bg_color = gui.widgets.get_widget("output").get_style().bg[gtk.STATE_NORMAL]
	color = colors[sum([ord(n) for n in nick]) % len(colors)]

	return contrast.contrast_render_foreground_color(bg_color, color)

def isHighlighted (server, text):
	highlightwords = config.get_list("chatting", "highlight_words")
	highlightwords.append(com.getOwnNick(server))

	search_text = text.lower()
	for word in highlightwords:
		i = search_text.find(word.lower())

		if i >= 0:
			return True

	return False

def createTab (server, name):
	tab = gui.tabs.searchTab(server, name)

	if not tab:
		if name[0] in sushi.support_chantypes(server):
			tab = gui.tabs.createChannel(server, name)
		else:
			tab = gui.tabs.createQuery(server, name)

		tab.connected = True
		gui.tabs.addTab(server, tab)
		lastLog(server, name)

	if tab.name != name:
		# the name of the tab differs from the
		# real nick, correct this.
		tab.name = name

	return tab

def getPrefix(server, channel, nick):
	tab = gui.tabs.searchTab(server, channel)

	if tab and tab.is_channel():
		return tab.nickList.getPrefix(nick)
	else:
		return ""
"""
Server signals
"""

def serverConnect(time, server):
	"""
		maki is connecting to a server.
	"""
	tab = gui.tabs.searchTab(server)

	if not tab:
		tab = gui.tabs.createServer(server)

		# add tab and update shortcuts only
		# if it's necessary
		gui.tabs.addTab(
			None, tab,
			update_shortcuts = config.get_bool("tekka","server_shortcuts"))


	if tab.connected:
		tab.connected = False

		channels = gui.tabs.getAllTabs(server)[1:]

		if channels:
			for channelTab in channels:
				if channelTab.is_channel():
					channelTab.joined=False
				channelTab.connected=False

	gui.serverPrint(time, server, "Connecting...")

	# TODO: implement status bar messages
	#gui.statusBar.push(gui.STATUSBAR_CONNECTING, "Connecting to %s" % server)

def serverConnected(time, server):
	"""
		maki connected successfuly to a server.
	"""
	tab = gui.tabs.searchTab(server)

	if not tab:
		tab = gui.tabs.createServer(server)
		gui.tabs.addTab(None, tab)

	tab.connected = True

	addChannels(server)

	# iterate over tabs, set the connected flag to queries
	for query in [tab for tab in gui.tabs.getAllTabs(server)[1:] if tab.is_query()]:
		query.connected = True

	# TODO: implement status bar messages
	#gui.statusBar.pop(gui.STATUSBAR_CONNECTING)

	gui.serverPrint(time, server, "Connected.")

def serverMOTD(time, server, message):
	"""
		Server is sending a MOTD
	"""
	if not message:
		return

	if not gui.tabs.searchTab(server):
		gui.tabs.addTab(None, gui.tabs.createServer(server))

	gui.serverPrint(time, server, gui.escape(message))

def list(time, server, channel, users, topic):
	"""
		Signal for /list command.
		Prints content of the listing.
	"""
	if not channel and not topic and users == -1:
		gui.serverPrint(time, server, "End of list.")
		return

	gui.serverPrint(time, server, \
		"%s: %d user; topic: \"%s\"" % \
		(gui.escape(channel), users, gui.escape(topic)))

"""
Signals for channel interaction
"""


def channelTopic(time, server, from_str, channel, topic):
	"""
		The topic was set on server "server" in channel "channel" by
		user "nick" to "topic".
		Apply this!
	"""
	nick = parse_from(from_str)[0]
	channelTab = gui.tabs.searchTab(server, channel)

	if not channelTab:
		raise Exception("Channel %s does not exist but emits topic signal." % channel)

	channelTab.topic = topic
	channelTab.topicsetter = nick

	if channelTab == gui.tabs.getCurrentTab():
		gui.setTopic(topic)

	if not nick:
		# this indicates if there was a topic setter or maki is
		# just reporting the topic to us.
		return

	if nick == com.getOwnNick(server):
		message = _(u"• You changed the topic to “%(topic)s”.")
	else:
		message = _(u"• %(nick)s changed the topic to “%(topic)s”.")

	gui.channelPrint(time, server, channel, message % { "nick": nick, "topic": gui.escape(topic) }, "action")

def channelBanlist(time, server, channel, mask, who, when):
	"""
		ban list signal.
	"""
	if not mask and not who and when == -1:
		gui.channelPrint(time, server, channel, "End of banlist.", "action")
		return

	timestring = mtime.strftime("%Y-%m-%d %H:%M:%S", mtime.localtime(when))

	gui.channelPrint(time, server, channel, \
		"%s by %s on %s" % \
		(gui.escape(mask), gui.escape(who), gui.escape(timestring)), "action")

"""
Signals for maki
"""

def makiShutdownSignal(time):
	gui.myPrint("Maki is shut down!")
	gui.setUseable(False)

"""
Signals for users
"""

def userAway(time, server):
	"""
		maki says that we are away.
	"""
	tab = gui.tabs.searchTab(server)

	if tab:
		tab.away = "WE ARE AWAY. HERE SHOULD BE A MESSAGE BUT IT'S NOT IMPLEMENTED YET, SRY!"


def userBack(time, server):
	"""
		maki says that we are back from away being.
	"""
	tab = gui.tabs.searchTab(server)

	if tab:
		tab.away = ""

def userAwayMessage(timestamp, server, nick, message):
	"""
		The user is away and the server gives us the message he left
		for us to see why he is away and probably when he's back again.
	"""
	gui.channelPrint(timestamp, server, nick, _(u"• %(nick)s is away (%(message)s).") % { "nick": nick, "message": gui.escape(message) }, "action")

def userMessage(timestamp, server, from_str, channel, message):
	"""
		PRIVMSGs are coming in here.
	"""
	nick = parse_from(from_str)[0]

	if nick.lower() == com.getOwnNick(server).lower():
		ownMessage(timestamp, server, channel, message)
		return

	elif channel.lower() == com.getOwnNick(server).lower():
		userQuery(timestamp, server, from_str, message)
		return

	message = gui.escape(message)

	if isHighlighted(server, message):
		# set mode to highlight and disable setting
		# of text color for the main message (would
		# override channelPrint() highlight color)

		type = "highlightmessage"
		messageString = message
		gui.setUrgent(True)
	else:
		# no highlight, normal message type and
		# text color is allowed.

		type = "message"
		messageString = "<font foreground='%s'>%s</font>" % (
			getTextColor(nick), message)

	gui.channelPrint(timestamp, server, channel,
		"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			getPrefix(server, channel, nick),
			getNickColor(nick),
			gui.escape(nick),
			messageString,
		), type)

def ownMessage(timestamp, server, channel, message):
	"""
		The maki user wrote something on a channel or a query
	"""
	createTab(server, channel)
	nick = com.getOwnNick(server)

	gui.channelPrint(timestamp, server, channel,
		"&lt;%s<font foreground='%s' weight='bold'>%s</font>&gt; <font foreground='%s'>%s</font>" % (
		getPrefix(server, channel, nick),
		config.get("colors","own_nick","#000000"),
		nick,
		config.get("colors","own_text","#000000"),
		gui.escape(message)))

def userQuery(timestamp, server, from_str, message):
	"""
		A user writes to us in a query.
	"""
	nick = parse_from(from_str)[0]

	createTab(server, nick)

	gui.channelPrint(timestamp, server, nick,
		"&lt;<font foreground='%s' weight='bold'>%s</font>&gt; %s" % (
			getNickColor(nick),
			gui.escape(nick),
			gui.escape(message)
		), "message")

	# queries are important
	gui.setUrgent(True)

def userMode(time, server, from_str, target, mode, param):
	"""
		Mode change on target from nick detected.
		nick and param are optional arguments and
		can be empty.

		As nemo:
			/mode #xesio +o nemo
		will result in:
			userMode(<time>,<server>,"nemo","#xesio","+o","nemo")

		TODO: has to be colored and gettexted (o.0)
	"""
	nick = parse_from(from_str)[0]

	# nick: /mode target +mode param

	if not nick:
		# only a mode listing
		gui.currentServerPrint(time, server,
			_("• Modes for %(target)s: %(mode)s") % {
				"target":target,
				"mode":mode},
			"action")

	else:
		actor = nick
		if nick == com.getOwnNick(server):
			actor = "You"

		tab = gui.tabs.searchTab(server, target)
		if not tab:
			# no channel/query found

			if param: param = " "+param

			gui.currentServerPrint(time, server,
				"• %(actor)s set %(mode)s%(param)s on %(target)s" % {
					"actor":actor,
					"mode":mode,
					"param":param,
					"target":target},
				"action")
		else:
			# suitable channel/query found, print it there

			type = "action"
			victim = target

			if victim == com.getOwnNick(server):
				victim = "you"
				type = "hightlightaction"

			updatePrefix(tab, param, mode)
			if param: param = " "+param

			gui.channelPrint(time, server, tab.name,
				"• %(actor)s set %(mode)s%(param)s on %(victim)s." % {
						"actor":actor,
						"mode":mode,
						"param":param,
						"victim":victim},
				type)


def userOper(time, server):
	"""
		yay, somebody gives the user oper rights.
	"""
	gui.currentServerPrint(time, server, "• You got oper access.")

def userCTCP(time, server,  from_str, target, message):
	"""
		A user sends a CTCP request to target.
		I don't know a case in which target is not a channel
		and not queried.
	"""
	nick = parse_from(from_str)[0]

	if nick.lower() == com.getOwnNick(server).lower():
		ownCTCP(time, server, target, message)
		return
	elif target.lower() == com.getOwnNick(server).lower():
		queryCTCP(time, server, from_str, message)
		return

	headline = _("CTCP from %(nick)s to Channel:") % {
		"nick":gui.escape(nick)}

	gui.channelPrint(time, server, target,
		"<font foreground='#00DD33'>%s</font> %s" %	(
			headline, gui.escape(message)))

def ownCTCP(time, server, target, message):
	"""
		The maki user sends a CTCP request to
		a channel or user (target).
	"""
	tab = gui.tabs.searchTab(server, target)

	if tab:
		# valid query/channel found, print it there

		nickColor = config.get("colors","own_nick","#000000")
		textColor = config.get("colors","own_text","#000000")

		gui.channelPrint(time, server, tab.name,
			"&lt;CTCP:<font foreground='%s' weight='bold'>%s</font>&gt; "
			"<font foreground='%s'>%s</font>" % \
				(nickColor, com.getOwnNick(server),
				textColor, gui.escape(message)))

	else:
		gui.serverPrint(time, server,
			_("CTCP request from you to %(target)s: %(message)s") % {
			"target":gui.escape(target),
			"message":gui.escape(message)})

def queryCTCP(time, server, from_str, message):
	"""
		A user sends us a CTCP request over a query.

		If no query window is open, send it to the server tab.
	"""
	nick = parse_from(from_str)[0]
	tab = gui.tabs.searchTab(server, nick)

	if tab:
		gui.channelPrint(time, server, tab.name, \
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s</font>&gt; "
				"<font foreground='%s'>%s</font>" % \
				(getNickColor(nick), gui.escape(nick),
				getTextColor(nick), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server, \
				"&lt;CTCP:<font foreground='%s' weight='bold'>%s</font>&gt; "
				"<font foreground='%s'>%s</font>" % \
				(getNickColor(nick), gui.escape(nick),
				getTextColor(nick), gui.escape(message)))

def ownNotice(time, server, target, message):
	"""
		if query channel with ``target`` exists, print
		the notice there, else print it on the current
		channel of the network which is identified by
		`server`
	"""
	tab = gui.tabs.searchTab(server, target)
	ownNickColor = config.get("colors","own_nick","#000000")
	ownNick = com.getOwnNick(server)

	if tab:
		gui.channelPrint(time, server, tab.name, \
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % \
				(getNickColor(target), gui.escape(target),
				getTextColor(target), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server,
			"&gt;<font foreground='%s' weight='bold'>%s</font>&lt; "
			"<font foreground='%s'>%s</font>" % \
				(getNickColor(target), gui.escape(target),
				getTextColor(target), gui.escape(message)))


def queryNotice(time, server, from_str, message):
	"""
		A user sends a notice directly to the maki user.
	"""
	nick = parse_from(from_str)[0]

	tab = gui.tabs.searchTab(server, nick)
	if tab:
		if tab.name != nick:
			# correct notation of tab name
			tab.name = nick

	if tab:
		gui.channelPrint(time, server, tab.name,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % \
				(getNickColor(nick), gui.escape(nick),
				getTextColor(nick), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server,
				"-<font foreground='%s' weight='bold'>%s</font>- "
				"<font foreground='%s'>%s</font>" % \
				(getNickColor(nick), gui.escape(nick),
				getTextColor(nick), gui.escape(message)))

def userNotice(time, server, from_str, target, message):
	"""
		A user noticed to a channel (target).
	"""
	nick = parse_from(from_str)[0]

	if nick.lower() == com.getOwnNick(server).lower():
		ownNotice(time, server, target, message)
		return
	elif target.lower() == com.getOwnNick(server).lower():
		queryNotice(time, server, from_str, message)
		return

	gui.channelPrint(time, server, target, \
			"-<font foreground='%s' weight='bold'>%s</font>- "
			"<font foreground='%s'>%s</font>" % \
			(getNickColor(nick), gui.escape(nick),
			getTextColor(nick), gui.escape(message)))

def ownAction(time, server, channel, action):

	createTab(server, channel)

	nickColor = config.get("colors","own_nick","#000000")
	textColor = config.get("colors","own_text","#000000")

	gui.channelPrint(time, server, channel,
		"<font foreground='%s' weight='bold'>%s</font> "
		"<font foreground='%s'>%s</font>" % \
			(nickColor, com.getOwnNick(server), textColor, gui.escape(action)))

def actionQuery(time, server, from_str, action):

	nick = parse_from(from_str)[0]

	createTab(server, nick)

	gui.channelPrint(time, server, nick,
		"%s %s" % (nick, gui.escape(action)))

	gui.setUrgent(True)

def userAction(time, server, from_str, channel, action):
	"""
		A user sent a action (text in third person)
	"""
	nick = parse_from(from_str)[0]

	if nick.lower() == com.getOwnNick(server).lower():
		ownAction(time, server, channel, action)
		return

	elif channel.lower() == com.getOwnNick(server).lower():
		actionQuery(time, server, from_str, action)
		return

	action = gui.escape(action)

	if isHighlighted(server, action):
		type = "highlightaction"
		actionString = action
		gui.setUrgent(True)
	else:
		type = "action"
		actionString = "<font foreground='%s'>%s</font>" % (
			getTextColor(nick), action)

	gui.channelPrint(time, server, channel,
		"<font foreground='%s' weight='bold'>%s</font> %s" % (
			getNickColor(nick), nick, actionString), type)

def userNick(time, server, from_str, newNick):
	"""
	A user (or the maki user) changed it's nick.
	If a query window for this nick on this server
	exists, it's name would be changed.
	"""
	nick = parse_from(from_str)[0]
	# find a query
	tab = gui.tabs.searchTab(server, nick)

	# rename query if found
	if tab and tab.is_query():
		tab.name = newNick

	# we changed the nick
	if not nick or newNick == com.getOwnNick(server):
		message = _(u"• You are now known as %(newnick)s.")

		# update the nick in the GUI
		currentServer, currentChannel = gui.tabs.getCurrentTabs()
		if currentServer and currentServer.name == server:
			gui.setNick(newNick)

	# someone else did
	else:
		message = _(u"• %(nick)s is now known as %(newnick)s.")

	# iterate over all channels and look if the nick is
	# present there. If true so rename him in nicklist cache.
	for tab in gui.tabs.getAllTabs(server)[1:]:
		if not nick or newNick == com.getOwnNick(server):
			doPrint = True
		else:
			doPrint = not "nick" in config.get_list("channel_%s_%s" % (server.lower(), tab.name.lower()), "hide")

		if tab.is_channel():
			if (nick in tab.nickList.getNicks()):
				tab.nickList.modifyNick(nick, newNick)
			else:
				continue

		if tab.is_query() and tab.name != newNick:
			continue

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % \
			(getNickColor(nick), gui.escape(nick))
		newNickString = "<font foreground='%s' weight='bold'>%s</font>" % \
			(getNickColor(newNick), gui.escape(newNick))

		gui.channelPrint(time, server, tab.name,
			message % {
				"nick": nickString,
				"newnick": newNickString
			},
			"action")

def userKick(time, server, from_str, channel, who, reason):
	"""
		signal emitted if a user got kicked.
		If the kicked user is ourself mark the channel as
		joined=False
	"""
	nick = parse_from(from_str)[0]
	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		print "userKick: channel '%s' does not exist." % (channel)
		return

	channelString = "<font foreground='%s'>%s</font>" % (
		getTextColor(channel), gui.escape(channel))

	nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
		getNickColor(nick), gui.escape(nick))

	reasonString = "<font foreground='%s'>%s</font>" % (
		getTextColor(nick), gui.escape(reason))

	if who == com.getOwnNick(server):
		tab.joined = False

		message = _(u"« You have been kicked from %(channel)s "
			u"by %(nick)s (%(reason)s)." % {
				"channel": channelString,
				"nick": nickString,
				"reason": reasonString })

		gui.channelPrint(time, server, channel, message, "highlightaction")

	else:
		tab.nickList.removeNick(who)

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

		whoString = "<font foreground='%s' weight='bold'>%s</font>" % (
			getNickColor(who), gui.escape(who))

		message = _(u"« %(who)s was kicked from %(channel)s by %(nick)s (%(reason)s).") % {
			"who": whoString,
			"channel": channelString,
			"nick": nickString,
			"reason": reasonString }

		gui.channelPrint(time, server, channel, message, "action")


def userQuit(time, server, from_str, reason):
	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False (as well as the
	connect-flags of the childs).

	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	nick = parse_from(from_str)[0]
	if nick == com.getOwnNick(server):
		# set the connected flag to False for the server
		serverTab = gui.tabs.searchTab(server)

		if not serverTab:
			# this happens if the tab is closed
			return

		serverTab.connected = False

		# walk through all channels and set joined = False on them
		channels = gui.tabs.getAllTabs(server)[1:]

		if not channels:
			return

		if reason:
			message = _(u"« You have quit (%(reason)s).")
		else:
			message = _(u"« You have quit.")

		# deactivate channels/queries
		for channelTab in channels:
			if channelTab.is_channel():
				channelTab.joined=False

			channelTab.connected=False

			gui.channelPrint(time, server, channelTab.name, message % {
					"reason": reason},
				"action")

	else: # another user quit the network

		if reason:
			message = _(u"« %(nick)s has quit (%(reason)s).")
		else:
			message = _(u"« %(nick)s has quit.")

		channels = gui.tabs.getAllTabs(server)[1:]

		if not channels:
			print "No channels but quit reported.. Hum wtf? o.0"
			return

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			getNickColor(nick),
			gui.escape(nick))

		reasonString = "<font foreground='%s'>%s</font>" % (
			getTextColor(nick),
			gui.escape(reason))

		message = message % {
			"nick": nickString,
			"reason": reasonString
		}

		# print in all channels where nick joined a message
		for channelTab in channels:
			doPrint = not "quit" in config.get_list("channel_%s_%s" % (
				server.lower(), channelTab.name.lower()), "hide")

			if channelTab.is_query():
				# on query with `nick` only print quitmessage

				if doPrint and channelTab.name.lower() == nick.lower():
					gui.channelPrint(time, server, channelTab.name,
						message, "action")

				# skip nickList modification for queries
				continue

			# search for the nick in the channel
			# and print the quit message if the
			# nick was found.
			nickList = channelTab.nickList
			nicks = nickList.getNicks() or []

			if nick in nicks:
				nickList.removeNick(nick)

				if gui.tabs.isActive(channelTab):
					# update gui display for usercount
					gui.setUserCount(len(nickList),
						nickList.get_operator_count())

				if doPrint:
					gui.channelPrint(time, server, channelTab.name,
						message, "action")


def userJoin(timestamp, server, from_str, channel):
	"""
	A user identified by "nick" joins the channel "channel" on
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	nick = parse_from(from_str)[0]

	if nick == com.getOwnNick(server):
		# we joined a channel, fetch nicks and topic, create
		# channel and print the log

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			tab = gui.tabs.createChannel(server, channel)

			if not gui.tabs.addTab(server, tab):
				print "adding tab for channel '%s' failed." % (channel)
				return

			lastLog(server, channel)

		tab.nickList.clear()

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

		tab.joined = True
		tab.connected = True

		if config.get_bool("tekka","switch_to_channel_after_join"):
			gui.tabs.switchToPath(tab.path)

		nickString = "You"
		channelString = "<font foreground='%s'>%s</font>" % (
			getTextColor(channel), gui.escape(channel))

		message = _(u"» You have joined %(channel)s.")

		doPrint = True

	else: # another one joined the channel

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			print "No tab for channel '%s' in userJoin (not me)."
			return

		message = _(u"» %(nick)s has joined %(channel)s.")

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			getNickColor(nick),
			gui.escape(nick))

		channelString = "<font foreground='%s'>%s</font>" % (
			getTextColor(channel),
			gui.escape(channel))


		tab.nickList.appendNick(nick)

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

		doPrint = not "join" in config.get_list("channel_%s_%s" % (
			server.lower(), channel.lower()), "hide")

	message = message % {
		"nick": nickString,
		"channel": channelString
		}

	if doPrint:
		gui.channelPrint(timestamp, server, channel, message, "action")

def userNames(timestamp, server, channel, nicks, prefixes):
	"""
	this signal is called for each nick in the channel.
	remove the nick to make sure it isn't there (hac--workaround),
	add the nick, fetch the prefix for it and at least
	update the user count.

	To avoid a non existent channel this method checks against
	a missing channel tab and adds it if needed.
	"""
	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		tab = gui.tabs.createChannel(server, channel)

		if not gui.tabs.addTab(server, tab):
			print "adding tab for channel '%s' failed." % (channel)
			return

		lastLog(server, channel)

		tab.joined = True
		tab.connected = True

	if not nicks:
		tab.nickList.sortNicks()
		return

	for i in xrange(len(nicks)):
		# FIXME
		tab.nickList.removeNick(nicks[i])
		tab.nickList.appendNick(nicks[i], sort=False)

		if prefixes[i]:
			tab.nickList.setPrefix(nicks[i], prefixes[i], sort=False)

	if gui.tabs.isActive(tab):
		gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())


def userPart(timestamp, server, from_str, channel, reason):
	"""
	A user parted the channel.

	If we are the user who parted, mark the channel
	as parted (joined=False)
	"""
	nick = parse_from(from_str)[0]

	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		# tab was closed
		return

	if nick == com.getOwnNick(server):
		# we parted

		channelString = "<font foreground='%s'>%s</font>" % (
			getTextColor(channel), gui.escape(channel))

		reasonString = "<font foreground='%s'>%s</font>" % (
			getTextColor(nick), gui.escape(reason))

		if reason:
			message = _(u"« You have left %(channel)s (%(reason)s).")
		else:
			message = _(u"« You have left %(channel)s.")

		tab.joined = False

		gui.channelPrint(timestamp, server, channel,
			message % {
				"channel": channelString,
				"reason": reasonString },
			"action")

	else: # another user parted

		nickString = "<font foreground='%s' weight='bold'>%s</font>" % (
			getNickColor(nick), gui.escape(nick))

		channelString = "<font foreground='%s'>%s</font>" % (
			getTextColor(channel), gui.escape(channel))

		reasonString = "<font foreground='%s'>%s</font>" % (
			getTextColor(nick), gui.escape(reason))

		if reason:
			message = _(u"« %(nick)s has left %(channel)s (%(reason)s).")
		else:
			message = _(u"« %(nick)s has left %(channel)s.")

		tab.nickList.removeNick(nick)

		if gui.tabs.isActive(tab):
			gui.setUserCount(len(tab.nickList), tab.nickList.get_operator_count())

		if not "part" in config.get_list("channel_%s_%s" % (server.lower(), channel.lower()), "hide"):
			gui.channelPrint(timestamp, server, channel,
				message % {
					"nick": nickString,
					"channel": channelString,
					"reason": reasonString
					},
				"action")

def noSuch(time, server, target, type):
	"""
	Signal is emitted if maki can't find the target on the server.
	"""

	tab = gui.tabs.searchTab(server, target)

	if type == "n":
		error = _(u"• %(target)s: No such nick/channel.") % { "target": gui.escape(target) }
	elif type == "s":
		error = _(u"• %(target)s: No such server.") % { "target": gui.escape(target) }
	elif type == "c":
		error = _(u"• %(target)s: No such channel.") % { "target": gui.escape(target) }

	if tab:
		gui.channelPrint(time, server, target, error)
	else:
		gui.serverPrint(time, server, error)

def cannotJoin(time, server, channel, reason):
	"""
		The channel could not be joined.
		reason : { l (full), i (invite only), b (banned), k (key) }
	"""
	message = _("Unknown reason")

	if reason == "l":
		message = _("The channel is full.")
	elif reason == "i":
		message = _("The channel is invite-only.")
	elif reason == "b":
		message = _("You are banned.")
	elif reason == "k":
		if config.get_bool("tekka", "ask_for_key_on_cannotjoin"):
			# open a input dialog which asks for the key
			d = keyDialog.KeyDialog(server, channel)
			result = d.run()

			if result == gtk.RESPONSE_OK:
				com.join(server, channel, d.entry.get_text())

			d.destroy()
			return
		else:
			message = _("You need the correct channel key.")

	gui.currentServerPrint (time, server,
		_("You can not join %(channel)s: %(reason)s" % {
			"channel":channel,
			"reason":message
			}
		))


def whois(time, server, nick, message):
	"""
		message = "" => end of whois
	"""
	if message:
		gui.serverPrint(time, server, _(u"[%(nick)s] %(message)s") % { "nick": gui.escape(nick), "message": gui.escape(message) })
	else:
		gui.serverPrint(time, server, _(u"[%(nick)s] End of whois.") % { "nick": gui.escape(nick) })
