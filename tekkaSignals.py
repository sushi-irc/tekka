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

class tekkaSignals(object):
	def __init__(self, com, gui):
		self.com = com
		self.gui = gui

		self.bus = self.com.get_bus()

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

		self.init_servers()
	
	def init_servers(self):
		servertree = self.gui.get_servertree()
		for server in self.com.fetch_servers():

			servertree.addServer(server)
			self.addChannels(server)
			
			if self.com.is_away(server, self.com.get_own_nick(server)):
				servertree.getObject(server).setAway(True)

	def addChannels(self, server):
		channels = self.com.fetch_channels(server)
		
		for channel in channels:
			nicks = self.com.fetch_nicks(server, channel)
			
			self.com.request_topic(server,channel)
			
			ret,iter = self.gui.get_servertree().addChannel(server, channel, nicks=nicks)

			obj = self.gui.get_servertree().getObject(server,channel)
			nicklist = obj.getNicklist()

			# channel already existant, settings
			# nicks, set the topic and set the joined flag
			if ret == 1:
				nicklist.clear()
				nicklist.addNicks(nicks)
				obj.setJoined(True)
			else:
				self.__lastLogHack(server,channel,10)

			self._prefixFetch(server,channel,nicklist,nicks)


	""" HELPER """

	def __lastLogHack(self, server, channel, lines):
		obj = self.gui.get_servertree().getObject(server,channel)
		buffer = obj.getBuffer()
		path = os.environ["HOME"]+"/.sushi/logs/%s/%s.txt" % (server,channel)
		try:
			f = file(path)
		except:
			return
		if not f: 
			return
		try:
			lines = f.readlines()[-lines:]
		except:
			return
		for line in lines:
			buffer.insert_html(buffer.get_end_iter(), "<font foreground=\"#DDDDDD\">%s</font>" % self.gui.escape(line))


	"""
	solution to set the prefixes in the nicklist of a new
	added server. The iter returned by addChannel() is
	passed to this function (chaniter) like the nicks
	and prefixes for the nicks were fetched and added to
	the channel-nicklist
	"""
	def _prefixFetch(self, server, channel, nicklist, nicks):
		for nick in nicks:
			prefix = self.com.fetch_prefix(server,channel,nick)
			if not prefix: 
				continue
			nicklist.setPrefix(nick, prefix, mass=True)
		nicklist.sortNicks()
	
	"""
	Check for a similar to "nick" named channel (case-insensitive) 
	and rename it to "nick"
	User: /query Nemo -> a new channel with Nemo opened
	nemo: Is answering to User
	The problem now is that there is no channel-tab named
	like "nemo". _simCheck() searches for a tab similar to
	nemo (Nemo) and renames it to "nemo".
	"""
	def _simCheck(self, server, nick):
		servertree = self.gui.get_servertree()
		check = servertree.getChannel(server, nick)
		if not check:
			simfound = False
			for schannel in servertree.getChannels(server):
				if schannel.lower() == nick.lower():
					servertree.renameChannel(server, schannel, nick)
					simfound = True
			if not simfound:
				servertree.addChannel(server,nick)

	"""
	checks if the mode is a prefix-mode. if a prefix mode is
	given the prefix-char is added.
	"""
	def _prefixMode(self, server, channel, nick, mode):
		if mode[1] not in ("q","a","o","h","v"):
			return
		nicklist = self.gui.get_servertree().getObject(server,channel).getNicklist()
		if not nicklist:
			return
		nicklist.setPrefix(nick, self.com.fetch_prefix(server,channel,nick))


	def getNickColor(self, nick):
		colors = self.gui.get_config().getNickColors()
		if not colors:
			return "#2222AA"
		return colors[ord(nick[0])%len(colors)]


	""" SERVER SIGNALS """

	def serverConnect(self, time, server):
		self.gui.get_servertree().addServer(server)
		self.gui.serverPrint(time, server, "Connecting...")
		self.gui.get_statusbar().push(2,"Connecting to %s" % server)

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		servertree = self.gui.get_servertree()

		obj = servertree.getObject(server)
		obj.setConnected(True)
		servertree.updateDescription(server,obj=obj)

		self.addChannels(server)

		self.gui.get_statusbar().pop(2)
		self.gui.serverPrint(time, server, "Connected.")

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		# TODO: clear nicklists of server if existant
		self.gui.get_servertree().addServer(server)
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

		if nick == self.com.get_own_nick(server):
			nick = "You"

		self.gui.channelPrint(time, server, channel, "%s changed the topic to '%s'" % (nick, self.gui.escape(topic)))

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.gui.myPrint("Maki is shutting down!")
		for server in self.gui.getServers():
			self.gui.removeServer(server)
			self.com.quit_server(server)

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
		color = self.getNickColor(nick)
		message = self.gui.escape(message)
		self.gui.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; %s" % (color,nick,message))

	def ownMessage(self, timestamp, server, channel, message):
		self.gui.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; <msg>%s</msg>" \
		% (self.gui.get_config().getColor("ownNick"), self.com.get_own_nick(server), self.gui.escape(message)))

	def ownQuery(self, timestamp, server, channel, message):
		self.ownMessage(timestamp,server,channel,message)

	def userQuery(self, timestamp, server, nick, message):
		self._simCheck(server,nick)
		self.userMessage(timestamp,server,nick,nick,message)

	def userMode(self, time, server, nick, target, mode, param):
		myNick = self.com.get_own_nick(server)

		act_color = self.gui.get_config().getColor("modeActNick")
		param_color = self.gui.get_config().getColor("modeParam")

		actnick = "<font foreground='%s'>%s</font>" % (act_color, self.gui.escape(nick))
		if nick == myNick:
			actnick = "You"

		if target == myNick:
			self.gui.serverPrint(time, server,"%s set <b>%s</b> on you." % (actnick, mode))
		else:
			# if param a user mode is set
			if param:
				nickwrap = "<font foreground='%s'>%s</font>" % (param_color, self.gui.escape(param))
				if param == myNick:
					nickwrap = "You"
				msg = "%s set <b>%s</b> to %s." % (actnick,mode,nickwrap)

				self._prefixMode(server,target,param,mode)
			# else a channel is the target
			else:
				msg = "%s set <b>%s</b> on %s." % (actnick,mode,target)
			self.gui.channelPrint(time, server, target, msg)

	def userCTCP(self, time, server,  nick, target, message):
		self.gui.channelPrint(time, server, target, \
			"<font foreground='#00DD33'>CTCP from %s to Channel:</font> %s" % \
				(self.gui.escape(nick), self.gui.escape(message)))

	def ownCTCP(self, time, server, target, message):
		channel = self.gui.get_servertree().getChannel(server,target)
		if channel:
			nick_color = self.gui.get_config().getColor("ownNick")
			self.gui.channelPrint(time, server, channel, \
				"&lt;CTCP:<font foreground='%s'>%s</foreground>&gt; %s" % \
					(nick_color, self.com.get_own_nick(server), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, "CTCP request from you to %s: %s" \
					% (self.gui.escape(target), self.gui.escape(message)))

	def queryCTCP(self, time, server, nick, message):
		channel = self.gui.get_servertree().getChannel(server,nick)
		if channel:
			self.gui.channelPrint(time, server, channel, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, \
					"&lt;CTCP:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def queryNotice(self, time, server, nick, message):
		channel = self.gui.get_servertree().getChannel(server,nick)
		if channel:
			self.gui.channelPrint(time, server, channel, \
					"&lt;Notice:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))
		else:
			self.gui.serverPrint(time, server, \
					"&lt;Notice:<font foreground='%s'>%s</font>&gt; %s" % \
					(self.getNickColor(nick), self.gui.escape(nick), self.gui.escape(message)))

	def userNotice(self, time, server, nick, target, message):
		if target == self.com.get_own_nick(server):
			self._simCheck(server,nick)
			self.userMessage(time, server, nick, nick, message)

	# user sent an /me
	def userAction(self, time, server, nick, channel, action):
		action = self.gui.escape(action)
		self.gui.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, new_nick):
		servertree = self.gui.get_servertree()
		channel = servertree.getChannel(server, nick)
		if channel:
			servertree.renameChannel(server, channel, new_nick)
		
		if nick == self.com.get_own_nick(server):
			nickwrap = "You are"
		else:
			nickwrap = "%s is" % nick
		
		nickchange = "%s now known as %s." % (nickwrap, new_nick)
		nickchange = self.gui.escape(nickchange)

		for channel in servertree.getChannels(server):
			nicklist = servertree.getObject(server,channel).getNicklist()
			if nick in nicklist.getNicks() or channel == nick:
				nicklist.modifyNick(nick, new_nick)
				self.gui.channelPrint(time, server, channel, nickchange)

	# user was kicked
	def userKick(self, time, server, nick, channel, who, reason):
		if reason:
			reason = "(%s)" % reason

		if who == self.com.get_own_nick(server):
			servertree = self.gui.get_servertree()
			obj = servertree.getObject(server,channel).setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)

			self.gui.channelPrint(time, server, channel, self.gui.escape(\
				"You have been kicked from %s by %s %s" % (channel,nick,reason)))
		else:
			self.gui.channelPrint(time, server, channel, self.gui.escape("%s was kicked from %s by %s %s" % (who,channel,nick,reason)))

	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False.
	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	def userQuit(self, time, server, nick, reason):
		servertree = self.gui.get_servertree()
		
		if nick == self.com.get_own_nick(server):
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
					"%s has quit%s." % (nick,reasonwrap))
	
	"""
	A user identified by "nick" joins the channel "channel" on 
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	def userJoin(self, timestamp, server, nick, channel):
		servertree = self.gui.get_servertree()

		if nick == self.com.get_own_nick(server):
			nicks = self.com.fetch_nicks(server,channel)
			self.com.request_topic(server, channel)

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
				self.__lastLogHack(server,channel,10)

			# fetch the prefixes and apply
			# them to the nicklist of the channel
			# identified by "iter"
			self._prefixFetch(server,channel,nicklist,nicks)

			nickwrap = "You have"
		else:
			nickwrap = "<font foreground='%s'>%s</font> has" % (self.gui.get_config().getColor("joinNick"), self.gui.escape(nick))
			servertree.getObject(server,channel).getNicklist().appendNick(nick)
		self.gui.channelPrint(timestamp, server, channel, "%s joined %s." % (nickwrap, channel))

	# user parted
	def userPart(self, timestamp, server, nick, channel, reason):
		servertree = self.gui.get_servertree()
		obj = servertree.getObject(server,channel)

		if not obj: # happens if part + tab close
			return

		if reason: 
			reason = " (%s)" % reason

		if nick == self.com.get_own_nick(server):
			self.gui.channelPrint(timestamp, server, channel, "You have left %s%s." % (channel,reason))
			
			obj.setJoined(False)
			servertree.updateDescription(server, channel, obj=obj)
		else:
			obj.getNicklist().removeNick(nick)
			self.gui.channelPrint(timestamp, server, channel, \
			"<font foreground='%s'>%s</font> has left %s%s." % (self.gui.get_config().getColor("partNick"), self.gui.escape(nick), self.gui.escape(channel), self.gui.escape(reason)))


