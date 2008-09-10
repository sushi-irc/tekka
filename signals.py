# vim: fenc=utf-8:ft=python
# coding: UTF-8

from gettext import gettext as _

from dbus import UInt64
import time as mtime

config = None
gui = None
com = None
sushi = None

# TODO:  config values like quit or part message should
# TODO:: be retrieved from maki and set to maki.

def setup(_config, _gui, _com):
	global config, com, gui, sushi

	config = _config
	gui = _gui
	com = _com

	sushi = com.sushi

	# Message-Signals
	sushi.connect_to_signal("message", userMessage)
	sushi.connect_to_signal("own_message", ownMessage)
	sushi.connect_to_signal("own_notice", ownNotice)
	sushi.connect_to_signal("query", userQuery)
	sushi.connect_to_signal("notice", userNotice)
	sushi.connect_to_signal("action", userAction)
	sushi.connect_to_signal("away_message", userAwayMessage)
	sushi.connect_to_signal("ctcp", userCTCP)
	sushi.connect_to_signal("own_ctcp", ownCTCP)
	sushi.connect_to_signal("query_ctcp", queryCTCP)
	sushi.connect_to_signal("query_notice", queryNotice)
	sushi.connect_to_signal("invalid_target", invalidTarget)

	# action signals
	sushi.connect_to_signal("part", userPart)
	sushi.connect_to_signal("join", userJoin)
	sushi.connect_to_signal("quit", userQuit)
	sushi.connect_to_signal("kick", userKick)
	sushi.connect_to_signal("nick", userNick)
	sushi.connect_to_signal("away", userAway)
	sushi.connect_to_signal("back", userBack)
	sushi.connect_to_signal("mode", userMode)
	sushi.connect_to_signal("oper", userOper)


	# Server-Signals
	sushi.connect_to_signal("connect", serverConnect)
	sushi.connect_to_signal("connected", serverConnected)
	sushi.connect_to_signal("reconnect", serverReconnect)
	sushi.connect_to_signal("motd", serverMOTD)
	sushi.connect_to_signal("list", list)
	sushi.connect_to_signal("whois", whois)

	# Channel-Signals
	sushi.connect_to_signal("topic", channelTopic)
	sushi.connect_to_signal("banlist", channelBanlist)

	# Maki signals
	sushi.connect_to_signal("shutdown", makiShutdownSignal)

	initServers()

def initServers():
	"""
		Adds all servers to tekka which are reported by maki.
	"""
	# in case we're reconnecting, clear all stuff
	gui.getWidgets().get_widget("serverTree").get_model().clear()

	for server in com.fetchServers():

		tab = gui.tabs.createServer(server)
		tab.connected = True

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
		nicks = com.fetchNicks(server, channel)
		topic = sushi.channel_topic(server, channel)

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			tab = gui.tabs.createChannel(server, channel)
			add = True



		tab.nickList.clear()
		tab.nickList.addNicks(nicks)
		tab.topic = topic
		# TODO: handle topic setter
		tab.joined=True
		tab.connected=True

		if add:
			gui.tabs.addTab(server, tab)
			lastLog(server, channel)

		fetchPrefixes(server, channel, tab.nickList, nicks)

	gui.updateServerTreeShortcuts()


def fetchPrefixes(server, channel, nicklist, nicks):
	"""
		Itearates over the list of nicks `nicks` and fetches the prefix
		for every nick. After successful fetch the method adds the prefix
		to the nick in the referenced nicklist `nicklist`
	"""
	for nick in nicks:
		prefix = com.fetchPrefix(server,channel,nick)
		if not prefix:
			continue
		nicklist.setPrefix(nick, prefix, sort=False)
	nicklist.sortNicks()


def lastLog(server, channel, lines=0):
	"""
		Fetch lines amount of history text for channel
		on server.
	"""
	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		return

	buffer = tab.buffer

	if not buffer:
		print "lastLog('%s','%s'): no buffer" % (server,channel)
		return

	for line in com.fetchLog(
				server,
				channel,
				UInt64(lines or config.get("chatting", "last_log_lines", default="0"))
				):
		buffer.insertHTML(buffer.get_end_iter(), \
		"<font foreground=\"#DDDDDD\">%s</font>" % gui.escape(line))

def updatePrefix(tab, nick, mode):
	"""
		checks if the mode is a prefix-mode (e.g. +o)
		If so, the prefix of the nick `nick` in channel `channel`
		will be updated (fetched).
	"""
	if not nick: return
	# FIXME: cache support_prefix()!
	if mode[1] in sushi.support_prefix(tab.server)[0]:
		tab.nickList.setPrefix(nick, com.fetchPrefix(tab.server, tab.name, nick))


def getNickColor(nick):
	"""
		Returns a static color for the nick given.
		The returned color depends on the color mapping
		set in config module.
	"""
	colors = config.get("nick_colors", default={})

	colors = colors.values()

	if not colors:
		return "#2222AA"

	return colors[sum([ord(n) for n in nick])%len(colors)]


"""
Server signals
"""

def serverConnect(time, server):
	"""
		maki is connecting to a server.
	"""

	if not gui.tabs.searchTab(server):
		gui.tabs.addTab(None, gui.tabs.createServer(server))

		if config.get("tekka","server_shortcuts"):
			# update is only neccessary if server tabs
			# shall be shortcutted
			gui.updateServerTreeShortcuts()

	gui.serverPrint(time, server, "Connecting...")

	# TODO: implement status bar messages
	#gui.statusBar.push(gui.STATUSBAR_CONNECTING, "Connecting to %s" % server)

def serverConnected(time, server, nick):
	"""
		maki connected successfuly to a server.
	"""
	tab = gui.tabs.searchTab(server)

	if not tab:
		tab = gui.tabs.createServer(server)
		gui.tabs.addTab(None, tab)

	tab.connected = True
	gui.updateServerTreeMarkup(tab.path)

	addChannels(server)

	# iterate over tabs, set the connected flag to queries
	for query in [tab for tab in gui.tabs.getAllTabs(server)[1:] if tab.is_query()]:
		query.connected = True
		gui.updateServerTreeMarkup(query.path)

	# TODO: implement status bar messages
	#gui.statusBar.pop(gui.STATUSBAR_CONNECTING)

	gui.serverPrint(time, server, "Connected.")

def serverReconnect(time, server):
	"""
		maki is reconnecting to a server.
	"""
	tab = gui.tabs.searchTab(server)

	if tab:
		if tab.connected:
			userQuit(time, server, com.getOwnNick(server), "Connection lost")

	else:
		gui.tabs.addTab(None, gui.tabs.createServer(server))

		if config.get("tekka","server_shortcuts"):
			gui.updateServerTreeShortcuts()

	gui.serverPrint(time, server, "Reconnecting to %s" % server)

def serverMOTD(time, server, message):
	"""
		Server is sending a MOTD
	"""
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


def channelTopic(time, server, nick, channel, topic):
	"""
		The topic was set on server "server" in channel "channel" by
		user "nick" to "topic".
		Apply this!
	"""
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
		gui.updateServerTreeMarkup(tab.path)


def userBack(time, server):
	"""
		maki says that we are back from away being.
	"""
	tab = gui.tabs.searchTab(server)

	if tab:
		tab.away = ""
		gui.updateServerTreeMarkup(tab.path)


def userAwayMessage(timestamp, server, nick, message):
	"""
		The user is away and the server gives us the message he left
		for us to see why he is away and probably when he's back again.
	"""
	gui.channelPrint(timestamp, server, nick, _(u"• %(nick)s is away (%(message)s).") % { "nick": nick, "message": gui.escape(message) }, "action")

def userMessage(timestamp, server, nick, channel, message):
	"""
		PRIVMSGs are coming in here.
	"""
	message = gui.escape(message)
	highlight_pre = ""
	highlight_post = ""

	# highlight text if own nick is in message
	i = -1

	# TODO:  make this global so the method hasn't
	# TODO:: to fetch the mapping every time
	highlightwords = config.get("highlight_words", default={})
	highlightwords = highlightwords.values()

	highlightwords.append(com.getOwnNick(server))

	for word in highlightwords:
		i = message.find(word)
		if i >= 0:
			break

	if i >= 0:
		type = "highlightmessage"
		highlight_pre = "<font foreground='#FF0000'>"
		highlight_post = "</font>"

		gui.setUrgent(True)
	else:
		type = "message"

	color = getNickColor(nick)

	tab = gui.tabs.searchTab(server, channel)

	if tab and tab.is_channel():
		prefix = tab.nickList.getPrefix(nick)

	else:
		prefix = " "

	gui.channelPrint(timestamp, server, channel,
		"%s&lt;%s<font foreground='%s'>%s</font>&gt; %s%s" % (
			highlight_pre,
			prefix,
			color,
			gui.escape(nick),
			message,
			highlight_post
		), type)

def ownMessage(timestamp, server, channel, message):
	"""
		The maki user wrote something on a channel or a query
	"""
	message = gui.escape(message)

	nick = com.getOwnNick(server)

	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		if channel[0] in sushi.support_chantypes(server):
			tab = gui.tabs.createChannel(server, channel)
		else:
			tab = gui.tabs.createQuery(server, channel)

		tab.connected = True
		gui.tabs.addTab(server, tab)
		lastLog(server, channel)

	if tab.is_channel():
		prefix = tab.nickList.getPrefix(nick)

		# <prefixnick> message
		gui.channelPrint(timestamp, server, channel,
			"&lt;%s<font foreground='%s'>%s</font>&gt; <font foreground='%s'>%s</font>" % (
			prefix,
			config.get("colors","own_nick","#000000"),
			nick,
			config.get("colors","own_nick","#000000"),
			message))

	elif tab.is_query():
		# <nick> message
		gui.channelPrint(timestamp, server, tab.name,
			"&lt;<font foreground='%s'>%s</font>&gt; <font foreground='%s'>%s</font>" % (
			config.get("colors","own_nick","#000000"),
			nick,
			config.get("colors","own_text","#000000"),
			message))


def userQuery(timestamp, server, nick, message):
	"""
		A user writes to us in a query.
	"""
	tab = gui.tabs.searchTab(server, nick)

	if not tab:
		tab = gui.tabs.createQuery(server, nick)
		tab.connected = True
		gui.tabs.addTab(server, tab)
		lastLog(server, nick)

	if tab.name != nick:
		# the name of the tab differs from the
		# real nick, correct this.

		corrected = tab.copy()
		corrected.name = nick

		gui.tabs.replaceTab(tab, corrected)

	# queries are important
	gui.setUrgent(True)

	userMessage(timestamp,server,nick,nick,message)

def userMode(time, server, nick, target, mode, param):
	"""
		Mode change on target from nick detected.
		nick and param are optional arguments and
		can be empty.

		As nemo:
			/mode #xesio +o nemo
		will result in:
			userMode(<time>,<server>,"nemo","#xesio","+o","nemo")
	"""

	# nick: /mode target +mode param

	if not nick:
		# only a mode listing
		gui.currentServerPrint(time, server, "• Modes for %s: %s" % (target, mode), "action")

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

def userCTCP(time, server,  nick, target, message):
	"""
		A user sends a CTCP request to target.
		I don't know a case in which target is not a channel
		and not queried.
	"""
	gui.channelPrint(time, server, target, \
		"<font foreground='#00DD33'>CTCP from %s to Channel:</font> %s" % \
			(gui.escape(nick), gui.escape(message)))

def ownCTCP(time, server, target, message):
	"""
		The maki user sends a CTCP request to
		a channel or user (target).
	"""
	tab = gui.tabs.searchTab(server, target)

	if tab:
		# valid query/channel found, print it there

		nickColor = config.get("colors","nick_color","#000000")
		gui.channelPrint(time, server, channel, \
			"&lt;CTCP:<font foreground='%s'>%s</foreground>&gt; %s" % \
				(nickColor, com.getOwnNick(server), gui.escape(message)))

	else:
		gui.serverPrint(time, server,
			"CTCP request from you to %s: %s" % (gui.escape(target),gui.escape(message)))

def queryCTCP(time, server, nick, message):
	"""
		A user sends us a CTCP request over a query.

		If no query window is open, send it to the server tab.
		FIXME: prove this for all methods which act like queryCTCP
	"""
	tab = gui.tabs.searchTab(server, nick)

	if tab:
		gui.channelPrint(time, server, tab.name, \
				"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server, \
				"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))

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
			"&gt;<font foreground='%s'>%s</font>&lt; %s" % \
				(getNickColor(target), gui.escape(target), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server, "&gt;<font foreground='%s'>%s</font>&lt; %s" \
				% (getNickColor(target), gui.escape(target), gui.escape(message)))


def queryNotice(time, server, nick, message):
	"""
		A user sends a notice directly to the maki user.
	"""

	tab = gui.tabs.searchTab(server, nick)
	if tab:
		if tab.name != nick:
			# correct notation of tab name
			cTab = tab.copy()
			cTab.name = nick
			gui.tabs.replaceTab(tab,cTab)

	if tab:
		gui.channelPrint(time, server, channel, \
				"-<font foreground='%s'>%s</font>- %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server, \
				"-<font foreground='%s'>%s</font>- %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))

def userNotice(time, server, nick, target, message):
	"""
		A user noticed to a channel (target).
	"""
	gui.channelPrint(time, server, target, \
			"-<font foreground='%s'>%s</font>- %s" % \
			(getNickColor(nick), gui.escape(nick), gui.escape(message)))

def userAction(time, server, nick, channel, action):
	"""
		A user sent a /me
	"""
	action = gui.escape(action)
	gui.channelPrint(time, server, channel, "%s %s" % (nick,action))

def userNick(time, server, nick, newNick):
	"""
		A user (or the maki user) changed it's nick.
		If a query window for this nick on this server
		exists, it's name would be changed.
	"""

	tab = gui.tabs.searchTab(server, nick)

	if tab and tab.is_query():
		cTab = tab.copy()
		cTab.name = newNick
		gui.tabs.replaceTab(tab, cTab)

	if newNick == com.getOwnNick(server):
		message = _(u"• You are now known as %(newnick)s.")

		# update the nick in the GUI
		gui.setNick(newNick)
	else:
		message = _(u"• %(nick)s is now known as %(newnick)s.")

	# iterate over all channels and look if the nick is
	# present there. If true so rename him in nicklist cache.
	for tab in gui.tabs.getAllTabs(server)[1:]:

		if tab.is_channel():
			if (nick in tab.nickList.getNicks()):
				tab.nickList.modifyNick(nick, newNick)
			else:
				continue

		if tab.is_query() and tab.name != newNick:
			continue

		gui.channelPrint(time, server, tab.name, message % {
			"nick": gui.escape(nick),
			"newnick": gui.escape(newNick)
			},
			"action")

def userKick(time, server, nick, channel, who, reason):
	"""
		signal emitted if a user got kicked.
		If the kicked user is ourself mark the channel as
		joined=False
	"""
	if reason:
		reason = "(%s)" % reason

	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		print "userKick: channel '%s' does not exist." % (channel)
		return

	if who == com.getOwnNick(server):
		tab.joined = False

		gui.updateServerTreeMarkup(tab.path)
		gui.channelPrint(time, server, channel, gui.escape(
			"« You have been kicked from %s by %s %s" % (channel,nick,reason)
			))

	else:
		tab.nickList.removeNick(who)
		gui.channelPrint(time, server, channel, gui.escape(
			"« %s was kicked from %s by %s %s" % (who,channel,nick,reason)),
			"action")


def userQuit(time, server, nick, reason):
	"""
		The user identified by nick quit on the server "server" with
		the reason "reason". "reason" can be empty ("").
		If we are the user all channels were set to joined=False and
		the server's connected-flag is set to False (as well as the
		connect-flags of the childs).
		If another user quits on all channels on which the user was on
		a message is generated.
	"""
	if nick == com.getOwnNick(server):
		# set the connected flag to False on the server
		serverTab = gui.tabs.searchTab(server)

		if not serverTab:
			# this happens if the tab is closed
			return

		serverTab.connected = False
		gui.updateServerTreeMarkup(serverTab.path)

		# walk through all channels and set joined = False on them
		channels = gui.tabs.getAllTabs(server)[1:]

		if not channels:
			return

		if reason:
			message = _(u"« You have quit (%(reason)s).")
		else:
			message = _(u"« You have quit.")

		for channelTab in channels:
			if channelTab.is_channel():
				channelTab.joined=False
			channelTab.connected=False
			gui.updateServerTreeMarkup(channelTab.path)
			gui.channelPrint(time, server, channelTab.name, message % { "reason": reason } )

	else:
		if reason:
			message = _(u"« %(nick)s has quit (%(reason)s).")
		else:
			message = _(u"« %(nick)s has quit.")

		channels = gui.tabs.getAllTabs(server)[1:]

		if not channels:
			print "No channels but quit reported.. Hum wtf? o.0"
			return

		# print in all channels where nick joined a message
		for channelTab in channels:

			if channelTab.is_query() and channelTab.name.lower() == nick.lower():
				# on query with `nick` only print quitmessage

				gui.channelPrint(time, server, channelTab.name,
				message % { "nick": gui.escape(nick), "reason": gui.escape(reason) }, "action")

				continue

			nickList = channelTab.nickList
			nicks = nickList.getNicks() or []

			if nick in nicks:
				nickList.removeNick(nick)

				gui.channelPrint(time, server, channelTab.name,
				message % { "nick": gui.escape(nick), "reason": gui.escape(reason) }, "action")


def userJoin(timestamp, server, nick, channel):
	"""
		A user identified by "nick" joins the channel "channel" on
		server "server.

		If the nick is our we add the channeltab and set properties
		on it, else we generate messages and stuff.
	"""

	if nick == com.getOwnNick(server):
		# we joined a channel, fetch nicks and topic, create
		# channel and such things...

		nicks = com.fetchNicks(server,channel)
		topic = sushi.channel_topic(server, channel) # XXX: does this really returns a topic?

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			tab = gui.tabs.createChannel(server, channel)

			if not gui.tabs.addTab(server, tab):
				print "adding tab for channel '%s' failed." % (channel)
				return

			lastLog(server, channel)
			gui.updateServerTreeShortcuts()

		tab.topic = topic
		tab.nickList.clear()
		tab.nickList.addNicks(nicks)
		tab.joined=True

		gui.updateServerTreeMarkup(tab.path)

		fetchPrefixes(server,channel,tab.nickList,nicks)

		if config.get("tekka","switch_to_channel_after_join"):
			gui.tabs.switchToPath(tab.path)

		message = _(u"» You have joined %(channel)s.")

	else:
		# another one joined the channel
		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			print "No tab for channel '%s' in userJoin (not me)."
			return

		message = _(u"» <font foreground='%(color)s'>%(nick)s</font> has joined %(channel)s.")

		tab.nickList.appendNick(nick)

	gui.channelPrint(timestamp, server, channel, message % { "color": config.get("colors","join_nick","#000000"), "nick": gui.escape(nick), "channel": gui.escape(channel) }, "action")

def userPart(timestamp, server, nick, channel, reason):
	"""
		A user parted the channel.
		If we are the user who parted, mark the channel
		as parted (joined=False)
	"""

	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		# tab was closed
		return

	if nick == com.getOwnNick(server):
		if reason:
			message = _(u"« You have left %(channel)s (%(reason)s).")
		else:
			message = _(u"« You have left %(channel)s.")

		tab.joined = False
		gui.updateServerTreeMarkup(tab.path)

		gui.channelPrint(timestamp, server, channel, message % { "channel": channel, "reason": reason }, "action")

	else:
		# another user parted
		if reason:
			message = _(u"« <font foreground='%(color)s'>%(nick)s</font> has left %(channel)s (%(reason)s).")
		else:
			message = _(u"« <font foreground='%(color)s'>%(nick)s</font> has left %(channel)s.")


		tab.nickList.removeNick(nick)
		gui.channelPrint(timestamp, server, channel,
			message % {
				"color": config.get("colors","part_nick","#000000"),
				"nick": gui.escape(nick),
				"channel": gui.escape(channel),
				"reason": gui.escape(reason)
				},
			"action")

def invalidTarget(time, server, target):
	"""
		Signal emitted if maki can't find the target
		on the server.
	"""
	tab = gui.tabs.searchTab(server, target)

	error = _(u"• %(target)s: No such nick/channel.") % { "target": gui.escape(target) }

	if tab:
		gui.channelPrint(time, server, target, error)
	else:
		gui.serverPrint(time, server, error)

def whois(time, server, nick, message):
	"""
		message = "" => end of whois
	"""
	if message:
		gui.serverPrint(time, server, _(u"[%(nick)s] %(message)s") % { "nick": gui.escape(nick), "message": gui.escape(message) })
	else:
		gui.serverPrint(time, server, _(u"[%(nick)s] End of whois.") % { "nick": gui.escape(nick) })
