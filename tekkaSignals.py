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

import dbus

class tekkaSignals(object):
	def __init__(self, com, gui):
		self.com = com
		self.gui = gui

		self.bus = self.com.getBus()

		if not self.bus:
			print "tekkaSignals: No bus."
			return

		# Message-Signals
		self.bus.add_signal_receiver(self.userMessage, "message")
		self.bus.add_signal_receiver(self.ownMessage, "own_message")
		self.bus.add_signal_receiver(self.ownQuery, "own_query")
		self.bus.add_signal_receiver(self.userQuery, "query")
		self.bus.add_signal_receiver(self.userNotice, "notice")
		self.bus.add_signal_receiver(self.userAction, "action")
		self.bus.add_signal_receiver(self.userAwayMessage, "away_message")
		self.bus.add_signal_receiver(self.userCTCP, "ctcp")
		self.bus.add_signal_receiver(self.ownCTCP, "own_ctcp")
		self.bus.add_signal_receiver(self.queryCTCP, "query_ctcp")
		self.bus.add_signal_receiver(self.queryNotice, "query_notice")

		# action signals
		self.bus.add_signal_receiver(self.userPart, "part")
		self.bus.add_signal_receiver(self.userJoin, "join")
		self.bus.add_signal_receiver(self.userQuit, "quit")
		self.bus.add_signal_receiver(self.userKick, "kick")
		self.bus.add_signal_receiver(self.userNick, "nick")
		self.bus.add_signal_receiver(self.userAway, "away")
		self.bus.add_signal_receiver(self.userBack, "back")
		self.bus.add_signal_receiver(self.userMode, "mode")

		# Server-Signals
		self.bus.add_signal_receiver(self.serverConnect, "connect")
		self.bus.add_signal_receiver(self.serverConnected, "connected")
		self.bus.add_signal_receiver(self.serverReconnect, "reconnect")
		self.bus.add_signal_receiver(self.serverMOTD, "motd")

		# Channel-Signals
		self.bus.add_signal_receiver(self.channelTopic, "topic")

		# Maki signals
		self.bus.add_signal_receiver(self.makiShutdownSignal, "shutdown")

		self.initServers()

	def initServers(self):
		servertree = self.gui.getServertree()
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

			self.com.requestTopic(server,channel)

			ret,iter = self.gui.getServertree().addChannel(server, channel, nicks=nicks)

			obj = self.gui.getServertree().getObject(server,channel)
			nicklist = obj.getNicklist()

			# channel already existant, settings
			# nicks, set the topic and set the joined flag
			if ret == 1:
				nicklist.clear()
				nicklist.addNicks(nicks)
				obj.setJoined(True)
			else:
				self.lastLog(server,channel,10)

			self._prefixFetch(server,channel,nicklist,nicks)


	""" HELPER """

	def lastLog(self, server, channel, lines):
		obj = self.gui.getServertree().getObject(server,channel)
		buffer = obj.getBuffer()
		for line in self.com.fetchLog(server, channel, dbus.UInt64(lines)):
			buffer.insertHTML(buffer.get_end_iter(), "<font foreground=\"#DDDDDD\">%s</font><br/>" % self.gui.escape(line))


	"""
	solution to set the prefixes in the nicklist of a new
	added server. The iter returned by addChannel() is
	passed to this function (chaniter) like the nicks
	and prefixes for the nicks were fetched and added to
	the channel-nicklist
	"""
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
		servertree = self.gui.getServertree()
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
		servertree = self.gui.getServertree()
		channel = self._simFind(server, nick)
		if channel:
			servertree.renameChannel(server, channel, nick)
		else:
			servertree.addChannel(server,nick)

	"""
	checks if the mode is a prefix-mode. if a prefix mode is
	given the prefix-char is added.
	"""
	def _prefixMode(self, server, channel, nick, mode):
		if mode[1] not in ("q","a","o","h","v"):
			return
		nicklist = self.gui.getServertree().getObject(server,channel).getNicklist()
		if not nicklist:
			return
		nicklist.setPrefix(nick, self.com.fetchPrefix(server,channel,nick))


	def getNickColor(self, nick):
		colors = self.gui.getConfig().getNickColors()
		if not colors:
			return "#2222AA"
		return colors[sum([ord(n) for n in nick])%len(colors)]


	""" SERVER SIGNALS """

	def serverConnect(self, time, server):
		self.gui.getServertree().addServer(server)
		self.gui.serverPrint(time, server, "Connecting...")
		self.gui.getStatusbar().push(self.gui.STATUSBAR_CONNECTING, "Connecting to %s" % server)

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		servertree = self.gui.getServertree()

		obj = servertree.getObject(server)
		obj.setConnected(True)
		servertree.updateDescription(server,obj=obj)

		self.addChannels(server)

		self.gui.getStatusbar().pop(self.gui.STATUSBAR_CONNECTING)
		self.gui.serverPrint(time, server, "Connected.")

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		# TODO: clear nicklists of server if existant
		self.gui.getServertree().addServer(server)
		self.gui.serverPrint(time, server, "Reconnecting to %s" % server)

	# the server is sending a MOTD
	def serverMOTD(self, time, server, message):
		self.gui.serverPrint(time, server, self.gui.escape(message))

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

		self.gui.channelPrint(time, server, channel, "%s changed the topic to '%s'" % (nick, self.gui.escape(topic)))

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.gui.myPrint("Maki is shutting down!")
		for server in self.gui.getServers():
			self.gui.removeServer(server)
			self.com.quitServer(server)

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
		if message.find(self.com.getOwnNick(server)) >= 0:
			type = "highlightmessage"
		else:
			type = "message"

		color = self.getNickColor(nick)
		message = self.gui.escape(message)

		self.gui.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; %s" % (color,nick,message), type)

	def ownMessage(self, timestamp, server, channel, message):
		self.gui.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; %s" \
		% (self.gui.getConfig().getColor("ownNick"), self.com.getOwnNick(server), self.gui.escape(message)))

	def ownQuery(self, timestamp, server, channel, message):
		self.ownMessage(timestamp,server,channel,message)

	def userQuery(self, timestamp, server, nick, message):
		self._simCheck(server,nick)
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
			self.gui.serverPrint(time, server,"%s set <b>%s</b> on you." % (actnick, mode))

		else:
			# if param a user mode is set
			if param:
				nickwrap = "<font foreground='%s'>%s</font>" % (paramColor, self.gui.escape(param))
				if param == myNick:
					nickwrap = "you"
					type = "highlightaction"

				msg = "%s set <b>%s</b> to %s." % (actnick,mode,nickwrap)

				self._prefixMode(server,target,param,mode)

			# else a channel is the target
			else:
				msg = "%s set <b>%s</b> on %s." % (actnick,mode,target)

			self.gui.channelPrint(time, server, target, msg, type)

	def userCTCP(self, time, server,  nick, target, message):
		self.gui.channelPrint(time, server, target, \
			"<font foreground='#00DD33'>CTCP from %s to Channel:</font> %s" % \
				(self.gui.escape(nick), self.gui.escape(message)))

	def ownCTCP(self, time, server, target, message):
		channel = self.gui.getServertree().getChannel(server,target)
		if channel:
			nickColor = self.gui.getConfig().getColor("ownNick")
			self.gui.channelPrint(time, server, channel, \
				"&lt;CTCP:<font foreground='%s'>%s</foreground>&gt; %s" % \
					(nickColor, self.com.getOwnNick(server), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, "CTCP request from you to %s: %s" \
					% (self.gui.escape(target), self.gui.escape(message)))

	def queryCTCP(self, time, server, nick, message):
		channel = self.gui.getServertree().getChannel(server,nick)
		if channel:
			self.gui.channelPrint(time, server, channel, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def queryNotice(self, time, server, nick, message):
		channel = self._simFind(server, nick)
		if channel:
			if channel != nick:
				self.gui.getServertree().renameChannel(server, channel, nick)
				channel = nick
		
		if channel:
			self.gui.channelPrint(time, server, channel, \
					"&lt;Notice:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, \
					"&lt;Notice:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def userNotice(self, time, server, nick, target, message):
		self.gui.channelPrint(time, server, target, \
				"&lt;Notice:<font foreground='%s'>%s</font>&gt; %s" % \
				(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	# user sent an /me
	def userAction(self, time, server, nick, channel, action):
		action = self.gui.escape(action)
		self.gui.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, newNick):
		servertree = self.gui.getServertree()
		channel = servertree.getChannel(server, nick)
		if channel:
			servertree.renameChannel(server, channel, newNick)

		if newNick == self.com.getOwnNick(server):
			nickwrap = "You are"
		else:
			nickwrap = "%s is" % nick

		nickchange = "%s now known as %s." % (nickwrap, newNick)
		nickchange = self.gui.escape(nickchange)

		for channel in servertree.getChannels(server):
			nicklist = servertree.getObject(server,channel).getNicklist()
			if nick in nicklist.getNicks() or channel == nick:
				nicklist.modifyNick(nick, newNick)
				self.gui.channelPrint(time, server, channel, nickchange, "action")

	# user was kicked
	def userKick(self, time, server, nick, channel, who, reason):
		if reason:
			reason = "(%s)" % reason

		servertree = self.gui.getServertree()
		obj = servertree.getObject(server,channel)

		if who == self.com.getOwnNick(server):
			obj.setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)
			self.gui.channelPrint(time, server, channel, self.gui.escape(\
				"You have been kicked from %s by %s %s" % (channel,nick,reason)))
		else:
			obj.getNicklist().removeNick(who)
			self.gui.channelPrint(time, server, channel, self.gui.escape("%s was kicked from %s by %s %s" % (who,channel,nick,reason)), "action")

	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False.
	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	def userQuit(self, time, server, nick, reason):
		servertree = self.gui.getServertree()

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

			for channel in channels:
				obj = servertree.getObject(server,channel)
				obj.setJoined(False)
				servertree.updateDescription(server,channel,obj=obj)
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
				nicklist = obj.getNicklist()

				nicks = nicklist.getNicks() or []

				if nick in nicks or nick == channel:
					nicklist.removeNick(nick)
					self.gui.channelPrint(time, server, channel, \
					"%s has quit%s." % (nick,reasonwrap), "action")

	"""
	A user identified by "nick" joins the channel "channel" on
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	def userJoin(self, timestamp, server, nick, channel):
		servertree = self.gui.getServertree()

		if nick == self.com.getOwnNick(server):
			nicks = self.com.fetchNicks(server,channel)
			self.com.requestTopic(server, channel)

			# returns the iter of the channel if added (ret=0)
			# or if it's already existent (ret=1) if ret is 0
			# the nicks and the topic are already applied, else
			# we set them manually.
			ret,iter = servertree.addChannel(server, channel, nicks=nicks)

			if not iter:
				print "userJoin(%s,%s,%s): No Server!" % (server,channel,nick)
				return

			obj = servertree.getObject(server,channel)
			if not obj:
				print "Could not get object"
				return
			nicklist = obj.getNicklist()

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
				self.lastLog(server,channel,10)

			# fetch the prefixes and apply
			# them to the nicklist of the channel
			# identified by "iter"
			self._prefixFetch(server,channel,nicklist,nicks)

			nickwrap = "You have"
		else:
			nickwrap = "<font foreground='%s'>%s</font> has" % (self.gui.getConfig().getColor("joinNick"), self.gui.escape(nick))
			servertree.getObject(server,channel).getNicklist().appendNick(nick)
		self.gui.channelPrint(timestamp, server, channel, "%s joined %s." % (nickwrap, channel), "action")

	# user parted
	def userPart(self, timestamp, server, nick, channel, reason):
		servertree = self.gui.getServertree()
		obj = servertree.getObject(server,channel)

		if not obj: # happens if part + tab close
			return

		if reason:
			reason = " (%s)" % reason

		if nick == self.com.getOwnNick(server):
			self.gui.channelPrint(timestamp, server, channel, "You have left %s%s." % (channel,reason))

			obj.setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)
		else:
			obj.getNicklist().removeNick(nick)
			self.gui.channelPrint(timestamp, server, channel, \
			"<font foreground='%s'>%s</font> has left %s%s." % (self.gui.getConfig().getColor("partNick"), self.gui.escape(nick), self.gui.escape(channel), self.gui.escape(reason)), "action")

