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

"""
This code handles all signals from maki and
translates them into gui-actions.
"""

from gettext import gettext as _

import dbus

import time as mtime

class tekkaSignals(object):
	def __init__(self, com, gui):
		self.com = com
		self.gui = gui

		self.sushi = self.com.getSushi()

		if not self.sushi:
			print "tekkaSignals: No sushi."
			return

		# Message-Signals
		self.sushi.connect_to_signal("message", self.userMessage)
		self.sushi.connect_to_signal("own_message", self.ownMessage)
		self.sushi.connect_to_signal("own_query", self.ownQuery)
		self.sushi.connect_to_signal("own_notice", self.ownNotice)
		self.sushi.connect_to_signal("query", self.userQuery)
		self.sushi.connect_to_signal("notice", self.userNotice)
		self.sushi.connect_to_signal("action", self.userAction)
		self.sushi.connect_to_signal("away_message", self.userAwayMessage)
		self.sushi.connect_to_signal("ctcp", self.userCTCP)
		self.sushi.connect_to_signal("own_ctcp", self.ownCTCP)
		self.sushi.connect_to_signal("query_ctcp", self.queryCTCP)
		self.sushi.connect_to_signal("query_notice", self.queryNotice)
		self.sushi.connect_to_signal("invalid_target", self.invalidTarget)

		# action signals
		self.sushi.connect_to_signal("part", self.userPart)
		self.sushi.connect_to_signal("join", self.userJoin)
		self.sushi.connect_to_signal("quit", self.userQuit)
		self.sushi.connect_to_signal("kick", self.userKick)
		self.sushi.connect_to_signal("nick", self.userNick)
		self.sushi.connect_to_signal("away", self.userAway)
		self.sushi.connect_to_signal("back", self.userBack)
		self.sushi.connect_to_signal("mode", self.userMode)
		self.sushi.connect_to_signal("oper", self.userOper)

		# Server-Signals
		self.sushi.connect_to_signal("connect", self.serverConnect)
		self.sushi.connect_to_signal("connected", self.serverConnected)
		self.sushi.connect_to_signal("reconnect", self.serverReconnect)
		self.sushi.connect_to_signal("motd", self.serverMOTD)
		self.sushi.connect_to_signal("list", self.list)

		# Channel-Signals
		self.sushi.connect_to_signal("topic", self.channelTopic)
		self.sushi.connect_to_signal("banlist", self.channelBanlist)

		# Maki signals
		self.sushi.connect_to_signal("shutdown", self.makiShutdownSignal)

		self.initServers()

	def initServers(self):
		servertree = self.gui.getServerTree()
		for server in self.com.fetchServers():

			servertree.addServer(server)
			self.addChannels(server)

			if self.com.isAway(server, self.com.getOwnNick(server)):
				obj = servertree.getObject(server)
				obj.setAway(True)
				servertree.serverDescription(server, obj.markup())

	def addChannels(self, server):
		channels = self.com.fetchChannels(server)

		for channel in channels:
			nicks = self.com.fetchNicks(server, channel)
			topic = self.sushi.channel_topic(server, channel)
			serverTree = self.gui.getServerTree()

			ret,iter = serverTree.addChannel(server, channel, nicks, topic)

			obj = serverTree.getObject(server,channel)
			nicklist = obj.getNickList()

			if ret == serverTree.ROW_EXISTS:
				# channel already existant, settings
				# nicks, set the topic and set the joined flag

				nicklist.clear()
				nicklist.addNicks(nicks)
				obj.setJoined(True)

			else:
				self.lastLog(server,channel)

			self._prefixFetch(server,channel,nicklist,nicks)


	""" HELPER """

	"""
	Fetch @lines of log from @channel on @server
	"""
	def lastLog(self, server, channel, lines=0):
		obj = self.gui.getServerTree().getObject(server,channel)
		buffer = obj.getBuffer()
		for line in self.com.fetchLog(server, channel, dbus.UInt64(lines or self.com.getConfig().lastLogLines)):
			buffer.insertHTML(buffer.get_end_iter(), "<font foreground=\"#DDDDDD\">%s</font>" % self.gui.escape(line))


	def _prefixFetch(self, server, channel, nicklist, nicks):
		for nick in nicks:
			prefix = self.com.fetchPrefix(server,channel,nick)
			if not prefix:
				continue
			nicklist.setPrefix(nick, prefix, mass=True)
		nicklist.sortNicks()

	"""
	Check for a similar to "nick" named channel (case-insensitive)
	User: /query Nemo -> a new channel with Nemo opened
	nemo: Is answering to User
	The problem now is that there is no channel-tab named
	like "nemo". _simCheck() searches for a tab similar to
	nemo (Nemo) and returns it so it can be renamed
	"""
	def _simFind(self, server, nick):
		servertree = self.gui.getServerTree()
		check = servertree.getChannel(server, nick)
		if check:
			return check
		else:
			simfound = False
			for schannel in servertree.getChannels(server):
				if schannel.lower() == nick.lower():
					return schannel
		return False

	"""
	Extends _simFind.
	If a similar channel is found it would be renamed
	otherwise a new channel with name "nick" is created.
	"""
	def _simCheck(self, server, nick):
		servertree = self.gui.getServerTree()
		channel = self._simFind(server, nick)
		if channel and channel != nick:
			servertree.renameChannel(server, channel, nick)
		elif not channel:
			servertree.addChannel(server,nick)
			self.lastLog(server, nick)

	"""
	checks if the mode is a prefix-mode. if a prefix mode is
	given the prefix-char is added.
	"""
	def _prefixMode(self, server, channel, nick, mode):
		if mode[1] not in ("q","a","o","h","v"):
			return
		nicklist = self.gui.getServerTree().getObject(server,channel).getNickList()
		if not nicklist:
			return
		nicklist.setPrefix(nick, self.com.fetchPrefix(server,channel,nick))


	"""
	Returns a static color for nick @nick
	"""
	def getNickColor(self, nick):
		colors = self.gui.getConfig().getNickColors()
		if not colors:
			return "#2222AA"
		return colors[sum([ord(n) for n in nick])%len(colors)]


	""" SERVER SIGNALS """

	def serverConnect(self, time, server):
		self.gui.getServerTree().addServer(server)
		self.gui.serverPrint(time, server, "Connecting...")
		self.gui.getStatusBar().push(self.gui.STATUSBAR_CONNECTING, "Connecting to %s" % server)

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		servertree = self.gui.getServerTree()

		servertree.addServer(server) # if it isn't added here, add it now

		obj = servertree.getObject(server)
		obj.setConnected(True)
		servertree.updateDescription(server,obj=obj)

		self.addChannels(server)

		self.gui.getStatusBar().pop(self.gui.STATUSBAR_CONNECTING)
		self.gui.serverPrint(time, server, "Connected.")

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		obj = self.gui.getServerTree().getObject(server)
		if obj and obj.getConnected():
			self.userQuit(time, server, self.com.getOwnNick(server), "Connection lost")
		else:
			self.gui.getServerTree().addServer(server)
		self.gui.serverPrint(time, server, "Reconnecting to %s" % server)

	# the server is sending a MOTD
	def serverMOTD(self, time, server, message):
		self.gui.getServerTree().addServer(server)
		self.gui.serverPrint(time, server, self.gui.escape(message))

	def list(self, time, server, channel, users, topic):
		if not channel and not topic and users == -1:
			self.gui.serverPrint(time, server, "End of list.")
			return
		self.gui.serverPrint(time, server, \
			"%s: %d user; topic: \"%s\"" % \
			(self.gui.escape(channel), users, self.gui.escape(topic)))

	""" CHANNEL SIGNALS """

	"""
	The topic was set on server "server" in channel "channel" by
	user "nick" to "topic".
	Apply this!
	"""
	def channelTopic(self, time, server, nick, channel, topic):

		self.gui.setTopic(time, server, channel, nick, topic)

		if not nick:
			return

		if nick == self.com.getOwnNick(server):
			nick = "You"

		self.gui.channelPrint(time, server, channel, "• %s changed the topic to '%s'" % (nick, self.gui.escape(topic)))

	def channelBanlist(self, time, server, channel, mask, who, when):
		if not mask and not who and when == -1:
			self.gui.channelPrint(time, server, channel, "End of banlist.")
			return

		timestring = mtime.strftime("%Y-%m-%d %H:%M:%S", mtime.localtime(when))

		self.gui.channelPrint(time, server, channel, \
			"%s by %s on %s" % \
			(self.gui.escape(mask), self.gui.escape(who), self.gui.escape(timestring)))

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.gui.myPrint("Maki is shutting down!")
		self.gui.makeWidgetsSensitive(False)

	""" USER SIGNALS """

	"""
	maki says that we are away.
	"""
	def userAway(self, time, server):
		self.gui.setAway(time,server)

	"""
	maki says that we are back from away being.
	"""
	def userBack(self, time, server):
		self.gui.setBack(time,server)

	"""
	The user is away and the server gives us the message he left
	for us to see why he is away and probably when he's back again.
	"""
	def userAwayMessage(self, timestamp, server, nick, message):
		self.gui.channelPrint(timestamp, server, nick, "%s is away: %s" % (nick,self.gui.escape(message)))

	# privmessages are received here
	def userMessage(self, timestamp, server, nick, channel, message):
		message = self.gui.escape(message)
		highlight_pre = ""
		highlight_post = ""

		# highlight text if own nick is in message
		i = -1
		highlightwords = self.gui.getConfig().highlightWords
		highlightwords.append(self.com.getOwnNick(server))
		for word in highlightwords:
			i = message.find(word)
			if i >= 0:
				break
		if i >= 0:
			type = "highlightmessage"
			highlight_pre = "<font foreground='#FF0000'>"
			highlight_post = "</font>"

			self.gui.highlightWindow()
		else:
			type = "message"

		color = self.getNickColor(nick)

		prefix = self.gui.getServerTree().getObject(server,channel).getNickList().getPrefix(nick)

		self.gui.channelPrint(timestamp, server, channel, \
		"%s&lt;%s<font foreground='%s'>%s</font>&gt; %s%s" % \
		(highlight_pre, prefix, color,self.gui.escape(nick), message, highlight_post), type)

	def ownMessage(self, timestamp, server, channel, message):
		message = self.gui.escape(message)

		nick = self.com.getOwnNick(server)

		try:
			prefix = self.gui.getServerTree().getObject(server,channel).getNickList().getPrefix(nick)

			self.gui.channelPrint(timestamp, server, channel, \
				"&lt;%s<font foreground='%s'>%s</font>&gt; <font foreground='%s'>%s</font>" \
				% (prefix, self.gui.getConfig().getColor("ownNick"), nick, self.gui.getConfig().getColor("ownText"), message))
		except AttributeError:
			# this happens if sendMessage is called to send a message
			# directly to a user (e.g. chanserv):
			# AttributeError: 'NoneType' object has no attribute 'getNickList'
			# and
			# AttributeError: 'NoneType' object has no attribute 'getBuffer'
			prefix = " "
			self.gui.currentServerPrint(timestamp, server, \
				"-%s<font foreground='%s'>%s</font>/<font foreground='%s'>%s</font>- <font foreground='%s'>%s</font>" \
				% (prefix, self.gui.getConfig().getColor("ownNick"), nick, self.getNickColor(channel), channel, self.gui.getConfig().getColor("ownText"), message))




	def ownQuery(self, timestamp, server, channel, message):
		self.ownMessage(timestamp,server,channel,message)

	def userQuery(self, timestamp, server, nick, message):
		self._simCheck(server,nick)

		# queries are important
		if not self.gui.getWindow().has_toplevel_focus():
			self.gui.getWindow().set_urgency_hint(True)

		self.userMessage(timestamp,server,nick,nick,message)

	def userMode(self, time, server, nick, target, mode, param):
		myNick = self.com.getOwnNick(server)

		actColor = self.gui.getConfig().getColor("modeActNick")
		paramColor = self.gui.getConfig().getColor("modeParam")

		type = "action"

		actnick = "<font foreground='%s'>%s</font>" % (actColor, self.gui.escape(nick))
		if nick == myNick:
			actnick = "You"

		if target == myNick:
			self.gui.serverPrint(time, server,"• %s set <b>%s</b> on you." % (actnick, mode))

		else:
			# if param a user mode is set
			if param:
				nickwrap = "<font foreground='%s'>%s</font>" % (paramColor, self.gui.escape(param))
				if param == myNick:
					nickwrap = "you"
					type = "highlightaction"

				msg = "• %s set <b>%s</b> to %s." % (actnick,mode,nickwrap)

				self._prefixMode(server,target,param,mode)

			# else a channel is the target
			else:
				msg = "• %s set <b>%s</b> on %s." % (actnick,mode,target)

			self.gui.channelPrint(time, server, target, msg, type)

	def userOper(self, time, server):
		self.gui.serverPrint(time, server, "You got oper access.")

	def userCTCP(self, time, server,  nick, target, message):
		self.gui.channelPrint(time, server, target, \
			"<font foreground='#00DD33'>CTCP from %s to Channel:</font> %s" % \
				(self.gui.escape(nick), self.gui.escape(message)))

	def ownCTCP(self, time, server, target, message):
		channel = self.gui.getServerTree().getChannel(server,target)
		if channel:
			nickColor = self.gui.getConfig().getColor("ownNick")
			self.gui.channelPrint(time, server, channel, \
				"&lt;CTCP:<font foreground='%s'>%s</foreground>&gt; %s" % \
					(nickColor, self.com.getOwnNick(server), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, "CTCP request from you to %s: %s" \
					% (self.gui.escape(target), self.gui.escape(message)))

	def queryCTCP(self, time, server, nick, message):
		channel = self.gui.getServerTree().getChannel(server,nick)
		if channel:
			self.gui.channelPrint(time, server, channel, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def ownNotice(self, time, server, target, message):
		# if query channel with ``target`` exists, print
		# the notice there, else print it with currentServerPrint

		channel = self.gui.getServerTree().getChannel(server,target)

		ownNickColor = self.gui.getConfig().getColor("ownNick")
		ownNick = self.com.getOwnNick(server)

		if channel:
			self.gui.channelPrint(time, server, channel, \
				"&gt;<font foreground='%s'>%s</font>&lt; %s" % \
					(self.getNickColor(target), self.gui.escape(target), self.gui.escape(message)))
		else:
			self.gui.currentServerPrint(time, server, "&gt;<font foreground='%s'>%s</font>&lt; %s" \
					% (self.getNickColor(target), self.gui.escape(target), self.gui.escape(message)))


	def queryNotice(self, time, server, nick, message):
		channel = self._simFind(server, nick)
		if channel:
			if channel != nick:
				self.gui.getServerTree().renameChannel(server, channel, nick)
				channel = nick

		if channel:
			self.gui.channelPrint(time, server, channel, \
					"-<font foreground='%s'>%s</font>- %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.currentServerPrint(time, server, \
					"-<font foreground='%s'>%s</font>- %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def userNotice(self, time, server, nick, target, message):
		self.gui.channelPrint(time, server, target, \
				"-<font foreground='%s'>%s</font>- %s" % \
				(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	# user sent an /me
	def userAction(self, time, server, nick, channel, action):
		action = self.gui.escape(action)
		self.gui.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, newNick):
		servertree = self.gui.getServerTree()
		channel = servertree.getChannel(server, nick)
		if channel:
			servertree.renameChannel(server, channel, newNick)

		if newNick == self.com.getOwnNick(server):
			nickwrap = "You are"
		else:
			nickwrap = "%s is" % nick

		nickchange = "• %s now known as %s." % (nickwrap, newNick)
		nickchange = self.gui.escape(nickchange)

		for channel in servertree.getChannels(server):
			nicklist = servertree.getObject(server,channel).getNickList()
			if nick in nicklist.getNicks() or channel == nick:
				nicklist.modifyNick(nick, newNick)
				self.gui.channelPrint(time, server, channel, nickchange, "action")

	# user was kicked
	def userKick(self, time, server, nick, channel, who, reason):
		if reason:
			reason = "(%s)" % reason

		servertree = self.gui.getServerTree()
		obj = servertree.getObject(server,channel)

		if who == self.com.getOwnNick(server):
			obj.setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)
			self.gui.channelPrint(time, server, channel, self.gui.escape(\
				"« You have been kicked from %s by %s %s" % (channel,nick,reason)))
		else:
			obj.getNickList().removeNick(who)
			self.gui.channelPrint(time, server, channel, self.gui.escape("« %s was kicked from %s by %s %s" % (who,channel,nick,reason)), "action")

	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False.
	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	def userQuit(self, time, server, nick, reason):
		servertree = self.gui.getServerTree()

		if nick == self.com.getOwnNick(server):
			# set the connected flag to False on the server
			obj = servertree.getObject(server)

			if not obj: # this happens if the tab is closed
				return

			obj.setConnected(False)
			servertree.updateDescription(server,obj=obj)

			# walk through all channels and set joined = False on them
			channels = servertree.getChannels(server)

			if not channels:
				return

			if reason:
				reason = " (%s)" % reason

			for channel in channels:
				obj = servertree.getObject(server,channel)
				obj.setJoined(False)
				servertree.updateDescription(server,channel,obj=obj)
				self.gui.channelPrint(time, server, channel, \
					"« You have quit%s." % reason)
		else:
			reasonwrap = ""
			if reason:
				reasonwrap = " (%s)" % reason

			channels = servertree.getChannels(server)

			if not channels:
				print "No channels but quit reported.. Hum wtf? o.0"
				return

			# print in all channels where nick joined a message
			for channel in channels:
				obj = servertree.getObject(server,channel)
				nicklist = obj.getNickList()

				nicks = nicklist.getNicks() or []

				if nick in nicks or nick == channel:
					nicklist.removeNick(nick)
					self.gui.channelPrint(time, server, channel, \
					"« %s has quit%s." % (nick,reasonwrap), "action")

	"""
	A user identified by "nick" joins the channel "channel" on
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	def userJoin(self, timestamp, server, nick, channel):
		servertree = self.gui.getServerTree()

		if nick == self.com.getOwnNick(server):
			nicks = self.com.fetchNicks(server,channel)
			topic = self.sushi.channel_topic(server, channel)

			# returns the iter of the channel if added (ret=0)
			# or if it's already existent (ret=1) if ret is 0
			# the nicks and the topic are already applied, else
			# we set them manually.
			ret,iter = servertree.addChannel(server, channel, nicks, topic)

			if not iter:
				print "userJoin(%s,%s,%s): No Server!" % (server,channel,nick)
				return

			obj = servertree.getObject(server,channel)
			if not obj:
				print "Could not get object"
				return
			nicklist = obj.getNickList()

			# not added, already existent.
			# set nicks to nicklist of the channel,
			# set the topic and set the "joined"-flag
			# on the channel. Then generate and set the
			# description.
			if ret == 1:
				nicklist.clear()
				nicklist.addNicks(nicks)
				obj.setJoined(True)
				servertree.updateDescription(server,channel,obj=obj)
			else:
				self.lastLog(server,channel)



			# fetch the prefixes and apply
			# them to the nicklist of the channel
			# identified by "iter"
			self._prefixFetch(server,channel,nicklist,nicks)

			nickwrap = "You have"
		else:
			nickwrap = "<font foreground='%s'>%s</font> has" % (self.gui.getConfig().getColor("joinNick"), self.gui.escape(nick))
			servertree.getObject(server,channel).getNickList().appendNick(nick)
		self.gui.channelPrint(timestamp, server, channel, "» %s joined %s." % (nickwrap, channel), "action")

	# user parted
	def userPart(self, timestamp, server, nick, channel, reason):
		servertree = self.gui.getServerTree()
		obj = servertree.getObject(server,channel)

		if not obj: # happens if part + tab close
			return

		if reason:
			reason = " (%s)" % reason

		if nick == self.com.getOwnNick(server):
			self.gui.channelPrint(timestamp, server, channel, "« You have left %s%s." % (channel,reason))

			obj.setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)
		else:
			obj.getNickList().removeNick(nick)
			self.gui.channelPrint(timestamp, server, channel, \
			"« <font foreground='%s'>%s</font> has left %s%s." % (self.gui.getConfig().getColor("partNick"), self.gui.escape(nick), self.gui.escape(channel), self.gui.escape(reason)), "action")

	def invalidTarget(self, time, server, target):
		channel = self._simFind(server, target)

		error = _("%s: No such nick/channel.") % (target)

		if channel:
			self.gui.channelPrint(time, server, channel, "• %s" % (error))
		else:
			self.gui.currentServerPrint(time, server, "• %s" % (error))
