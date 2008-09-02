# vim: fenc=utf-8:ft=python
# coding: UTF-8

from gettext import gettext as _

from dbus import UInt64
import time as mtime

config = None
gui = None
com = None
sushi = None

# FIXME: after reconnect channels were added again

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
	sushi.connect_to_signal("own_query", ownQuery)
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
			tab.setAway(True)

		gui.tabs.addTab(None, tab)

		addChannels(server)

def addChannels(server):
	"""
		Adds all channels to tekka wich are reported by maki.
	"""
	channels = com.fetchChannels(server)

	for channel in channels:

		nicks = com.fetchNicks(server, channel)
		topic = sushi.channel_topic(server, channel)

		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			tab = gui.tabs.createChannel(server, channel)

		tab.nickList.clear()
		tab.nickList.addNicks(nicks)
		tab.topic = topic
		# TODO: handle topic setter
		tab.joined=True

		fetchPrefixes(server, channel, tab.nickList, nicks)			

		gui.tabs.addTab(server, tab)

		lastLog(server,channel)


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
				UInt64(lines or config.get("chatting", "lastLogLines", default="0"))
				):
		buffer.insertHTML(buffer.get_end_iter(), \
		"<font foreground=\"#DDDDDD\">%s</font>" % gui.escape(line))

def _updatePrefix(server, channel, nick, mode):
	"""
		checks if the mode is a prefix-mode. if a prefix mode is
		given the prefix-char is added.
	"""
	if mode[1] in ("q","a","o","h","v"):
		nickList = gui.tabs.searchTab(server,channel).nickList

		if not nickList:
			return
		
		nickList.setPrefix(nick, com.fetchPrefix(server, channel, nick))


def getNickColor(nick):
	"""
		Returns a static color for the nick given.
		The returned color depends on the color mapping
		set in config module.
	"""
	colors = config.get("nickColors", default={})

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
		gui.tabs.addTab(tab)

	tab.connected = True
	gui.updateServerTreeMarkup(tab.path)

	addChannels(server)

	# TODO: implement status bar messages
	#gui.statusBar.pop(gui.STATUSBAR_CONNECTING)

	gui.serverPrint(time, server, "Connected.")

def serverReconnect(time, server):
	"""
		maki is reconnecting to a server.
	"""
	tab = gui.tabs.searchTab(server)

	if tab and tab.connected:
		userQuit(time, server, com.getOwnNick(server), "Connection lost")

	elif not tab:
		gui.tabs.addTab(None, gui.tabs.createServer(server))

	gui.serverPrint(time, server, "Reconnecting to %s" % server)

def serverMOTD(time, server, message):
	"""
		Server is sending a MOTD
	"""
	if not gui.tabs.searchTab(server):
		gui.tabs.addTab(None, gui.createServer(server))

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

	gui.setTopic(topic)

	if not nick:
		# this indicates if there was a topic setter or maki is
		# just reporting the topic to us.
		return

	if nick == com.getOwnNick(server):
		nick = "You"

	gui.channelPrint(time, server, channel, "• %s changed the topic to '%s'" % (nick, gui.escape(topic)), "action")

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
	gui.myPrint("Maki is shutting down!")
	gui.setUseable(False)

"""
Signals for users
"""

def userAway(time, server):
	"""
		maki says that we are away.
	"""
	tab = gui.tabs.searchTab(None, server)

	if tab:
		tab.away = "WE ARE AWAY. HERE SHOULD BE A MESSAGE BUT IT'S NOT IMPLEMENTED YET, SRY!"
		gui.updateServerTreeMarkup(tab.path)


def userBack(time, server):
	"""
		maki says that we are back from away being.
	"""
	tab = gui.tabs.searchTab(None, server)

	if tab:
		tab.away = ""
		gui.updateServerTreeMarkup(tab.path)


def userAwayMessage(timestamp, server, nick, message):
	"""
		The user is away and the server gives us the message he left
		for us to see why he is away and probably when he's back again.
	"""
	gui.channelPrint(timestamp, server, nick, "%s is away: %s" % (nick, gui.escape(message)), "action")

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
	highlightwords = config.get("highlightWords", default={})
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
		The maki user wrote something.
	"""
	message = gui.escape(message)

	nick = com.getOwnNick(server)

	tab = gui.tabs.searchTab(server, channel)

	if not tab:
		raise Exception("This should not happen. No tab in ownMessage(%s,%s)." % \
			(server,channel))

	if tab.is_channel():
		prefix = tab.nickList.getPrefix(nick)

		# <prefixnick> message
		gui.channelPrint(timestamp, server, channel, \
			"&lt;%s<font foreground='%s'>%s</font>&gt; <font foreground='%s'>%s</font>" % (
			prefix,
			config.get("colors","ownNick","#000000"),
			nick,
			config.get("colors","ownNick","#000000"),
			message))

	elif tab.is_query():
		# -nick- message
		gui.currentServerPrint(timestamp, server, \
			"-<font foreground='%s'>%s</font>/<font foreground='%s'>%s</font>- <font foreground='%s'>%s</font>" % (
			config.get("colors","ownNick","#000000"),
			nick,
			getNickColor(channel),
			channel,
			config.get("colors","ownText","#000000"),
			message))


def ownQuery(timestamp, server, channel, message):
	"""
		The maki user writes to a query.
	"""
	ownMessage(timestamp,server,channel,message)

def userQuery(timestamp, server, nick, message):
	"""
		A user writes to us in a query.
	"""
	tab = gui.searchTab(server, nick)

	if not tab:
		tab = createQuery(server, nick)
		gui.addTab(server, tab)
	
	if tab.name != nick:
		# the name of the tab differs from the
		# real nick, correct this.

		corrected = tab.copy()
		corrected.name = nick

		gui.replaceTab(tab, corrected)

	# queries are important
	gui.setUrgent(True)

	userMessage(timestamp,server,nick,nick,message)

def userMode(time, server, nick, target, mode, param):
	"""
		zomg.
	"""
	# FIXME: broken
	return
	myNick = com.getOwnNick(server)

	actColor = gui.getConfig().getColor("modeActNick")
	paramColor = gui.getConfig().getColor("modeParam")

	type = "action"

	actnick = "<font foreground='%s'>%s</font>" % (actColor, gui.escape(nick))
	if nick == myNick:
		actnick = "You"

	if target == myNick:
		gui.serverPrint(time, server,"• %s set <b>%s</b> on you." % (actnick, mode))

	else:
		# if param a user mode is set
		if param:
			nickwrap = "<font foreground='%s'>%s</font>" % (paramColor, gui.escape(param))
			if param == myNick:
				nickwrap = "you"
				type = "highlightaction"

			msg = "• %s set <b>%s</b> to %s." % (actnick,mode,nickwrap)

			_updatePrefix(server, target, param, mode)

		# else a channel is the target
		else:
			msg = "• %s set <b>%s</b> on %s." % (actnick,mode,target)

		gui.channelPrint(time, server, target, msg, type)

def userOper(time, server):
	"""
		yay, somebody gives the user oper rights.
	"""
	gui.serverPrint(time, server, "You got oper access.")

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
	# FIXME: BR=KEN

	channel = gui.serverTree.getChannel(server,target)
	if channel:
		nickColor = gui.getConfig().getColor("ownNick")
		gui.channelPrint(time, server, channel, \
			"&lt;CTCP:<font foreground='%s'>%s</foreground>&gt; %s" % \
				(nickColor, com.getOwnNick(server), gui.escape(message)))
	else:
		gui.serverPrint(time, server, "CTCP request from you to %s: %s" \
				% (gui.escape(target), gui.escape(message)))

def queryCTCP(time, server, nick, message):
	"""
		A user sends us a CTCP request over a query.

		If no query window is open, send it to the server tab.
		FIXME: prove this for all methods which act like queryCTCP
	"""
	channel = gui.serverTree.getChannel(server,nick)
	# FIXME: BR=KEN
	
	if channel:
		gui.channelPrint(time, server, channel, \
				"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))
	else:
		gui.serverPrint(time, server, \
				"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
				(getNickColor(nick), gui.escape(nick), gui.escape(message)))

def ownNotice(time, server, target, message):
	"""
		if query channel with ``target`` exists, print
		the notice there, else print it on the current
		channel of the network which is identified by 
		`server`
	"""
	# FIXME: BR=KEN

	channel = gui.serverTree.getChannel(server,target)

	ownNickColor = gui.getConfig().getColor("ownNick")
	ownNick = com.getOwnNick(server)

	if channel:
		gui.channelPrint(time, server, channel, \
			"&gt;<font foreground='%s'>%s</font>&lt; %s" % \
				(getNickColor(target), gui.escape(target), gui.escape(message)))
	else:
		gui.currentServerPrint(time, server, "&gt;<font foreground='%s'>%s</font>&lt; %s" \
				% (getNickColor(target), gui.escape(target), gui.escape(message)))


def queryNotice(time, server, nick, message):
	"""
		A user sends a notice directly to the maki user.
	"""
	# FIXME: BR=KEN
	return

	channel = _simFind(server, nick)
	if channel:
		if channel != nick:
			gui.serverTree.renameChannel(server, channel, nick)
			channel = nick

	if channel:
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

	if tab:
		cTab = tab.copy()
		cTab.name = newNick
		gui.tabs.replaceTab(tab, cTab)

	if newNick == com.getOwnNick(server):
		nickwrap = "You are"
	else:
		nickwrap = "%s is" % (nick)

	nickchange = "• %s now known as %s." % (nickwrap, newNick)
	nickchange = gui.escape(nickchange)

	# iterate over all channels and look if the nick is
	# present there. If true so rename him in nicklist cache.
	for tab in gui.tabs.getAllTabs(server)[1:]:
		if (nick in tab.nickList.getNicks()) or (tab.name.lower() == nick.lower()):
			tab.nickList.modifyNick(nick, newNick)
			gui.channelPrint(time, server, tab.name, nickchange, "action")

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
		the server's connected-flag is set to False.
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
			reason = " (%s)" % reason

		for channelTab in channels:
			channelTab.joined=False
			gui.updateServerTreeMarkup(channelTab.path)
			gui.channelPrint(time, server, channelTab.name, "« You have quit%s." % reason)

	else:
		reasonwrap = ""
		if reason:
			reasonwrap = " (%s)" % reason

		channels = gui.tabs.getAllTabs(server)[1:]

		if not channels:
			print "No channels but quit reported.. Hum wtf? o.0"
			return

		# print in all channels where nick joined a message
		for channelTab in channels:
			nickList = channelTab.nickList
			nicks = nickList.getNicks() or []

			if nick in nicks or nick.lower() == channelTab.name.lower():
				nickList.removeNick(nick)
				gui.channelPrint(time, server, channelTab.name, \
				"« %s has quit%s." % (nick,reasonwrap), "action")


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

		tab.topic = topic
		tab.nickList.clear()
		tab.nickList.addNicks(nicks)
		tab.joined=True

		gui.updateServerTreeMarkup(tab.path)

		fetchPrefixes(server,channel,tab.nickList,nicks)

		nickwrap = "You have"

	else:
		# another one joined the channel
		tab = gui.tabs.searchTab(server, channel)

		if not tab:
			print "No tab for channel '%s' in userJoin (not me)."
			return

		nickwrap = "<font foreground='%s'>%s</font> has" % (
			config.get("colors","joinNick","#000000"),
			gui.escape(nick)
			)

		tab.nickList.appendNick(nick)

	gui.channelPrint(timestamp, server, channel, "» %s joined %s." % (nickwrap, channel), "action")

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

	if reason:
		reason = " (%s)" % reason

	if nick == com.getOwnNick(server):
		tab.joined = False
		gui.updateServerTreeMarkup(tab.path)

		gui.channelPrint(timestamp, server, channel, "« You have left %s%s." % (channel,reason), "action")

	else:
		# another user parted
		
		tab.nickList.removeNick(nick)
		gui.channelPrint(timestamp, server, channel,
			"« <font foreground='%s'>%s</font> has left %s%s." % (
				config.get("colors","partNick","#000000"),
				gui.escape(nick),
				gui.escape(channel),
				gui.escape(reason)
			),
			"action")

def invalidTarget(time, server, target):
	"""
		Signal emitted if maki can't find the target
		on the server.
	"""
	tab = gui.tabs.searchTab(server, target)

	error = _("%s: No such nick/channel.") % (target)

	if tab:
		gui.channelPrint(time, server, channel, "• %s" % (error))
	else:
		gui.currentServerPrint(time, server, "• %s" % (error))
