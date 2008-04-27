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

import sys
import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop

class tekkaCom(object):
	def __init__(self):
		dbus_loop = DBusGMainLoop()
		self.bus = dbus.SessionBus(mainloop=dbus_loop)

		self._connectMaki()

		self.commands = {
		 "connect" : self.makiConnect,
			"nick" : self.makiNick,
			"part" : self.makiPart,
			"join" : self.makiJoin,
			"me"   : self.makiAction,
			"kick" : self.makiKick,
			"mode" : self.makiMode,
			"topic": self.makiTopic,
			"quit" : self.makiQuit,
			"away" : self.makiAway,
			"back" : self.makiBack,
			"oper" : self.makiOper,
			"kill" : self.makiKill,
			"query": self.tekkaQuery,
			"clear": self.tekkaClear
		}

		self.myNick = {}

	# connect to maki over dbus
	def _connectMaki(self):
		self.proxy = None

		try:
			self.proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
		except dbus.exceptions.DBusException, e:
			print e
			print "Is maki running?"
			
		if not self.proxy:
			sys.exit(1)

		# Message-Signals
		self.bus.add_signal_receiver(self.userMessage, "message")
		self.bus.add_signal_receiver(self.ownMessage, "own_message")
		self.bus.add_signal_receiver(self.userQuery, "query")
		self.bus.add_signal_receiver(self.userNotice, "notice")
		self.bus.add_signal_receiver(self.userAction, "action")
		self.bus.add_signal_receiver(self.userAwayMessage, "away_message")

		# action signals
		self.bus.add_signal_receiver(self.userPart, "part")
		self.bus.add_signal_receiver(self.userJoin, "join")
		self.bus.add_signal_receiver(self.userQuit, "quit")
		self.bus.add_signal_receiver(self.userKick, "kick")
		self.bus.add_signal_receiver(self.userNick, "nick")
		self.bus.add_signal_receiver(self.userAway, "away")
		self.bus.add_signal_receiver(self.userBack, "back")
		self.bus.add_signal_receiver(self.userCTCP, "ctcp")
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

	
	def sendText(self, text):
		if not text:
			return

		if text[0] == "/" and text[1] != "/":
			self.parseCommand(text[1:])
		else:
			if self.proxy:
				server,channel = self.getCurrentChannel()
				if not server:
					self.myPrint("could not determine server.")
					return
				if not channel:
					self.myPrint("would send to server directly.")
				else:
					if text[0:2] == "//":
						text = text[1:]
					self.proxy.message(server,channel,text)

	""" GENERIC CONNECTION STUFF """

	def getNicksFromMaki(self, server, channel):
		if not self.proxy: return None
		return self.proxy.nicks(server,channel)

	def getNickFromMaki(self, server):
		if not self.proxy:
			return None
		return self.proxy.own_nick(server)

	def getNick(self, server):
		if self.myNick.has_key(server):
			return self.myNick[server]
		return None

	def setNick(self, server, nickname):
		self.myNick[server] = nickname

	def addServers(self):
		servers = self.proxy.servers()

		if not servers:
			return

		for server in servers:
			# addServer in tekkaMain
			self.addServer(server)
			self.addChannels(server)
			self.setNick(server, self.getNickFromMaki(server))
			
			if self.isAway(server, self.getNick(server)):
				self.getObject(server).setAway(True)

	def addChannels(self, server):
		channels = self.proxy.channels(server)
		
		for channel in channels:
			nicks = self.getNicksFromMaki(server, channel)
			topic = self.getTopic(server,channel)
			
			ret,iter = self.addChannel(server, channel, nicks=nicks, topic=topic)

			obj = self.getObject(server,channel)
			nicklist = obj.getNicklist()

			# channel already existant, settings
			# nicks, set the topic and set the joined flag
			if ret == 1:
				nicklist.clear()
				nicklist.addNicks(nicks)
				obj.setTopic(topic)
				obj.setJoined(True)
			else:
				self.__lastLogHack(server,channel,10)

			self._prefixFetch(server,channel,nicklist,nicks)

	def isAway(self, server, nick):
		return self.proxy.user_away(server, nick)
	
	def getTopic(self, server, channel):
		return self.proxy.topic(server,channel,"")

	def userChannelPrefix(self, server, channel, nick):
		if not self.proxy: return ""
		return self.proxy.user_channel_prefix(server,channel,nick) 


	def getChannelAutojoin(self, server, channel):
		domain = "servers/%s" % server
		return self.proxy.sushi_get(domain, channel, "autojoin")

	def setAutojoin(self, server, channel, switch):
		domain = "servers/%s" % server
		if switch: switch = "true"
		else: switch = "false"
		self.proxy.sushi_set(domain, channel, "autojoin", switch)

	""" SERVER CREATION """

	def createServer(self, smap):
		domain = "servers/%s" % smap["servername"]
		del smap["servername"]
		for (k,v) in smap.items():
			if not v:
				self.proxy.sushi_remove(domain, "server", k)
			else:
				self.proxy.sushi_set(domain, "server", k, v)

	def deleteServer(self, name):
		domain = "servers/%s" % name
		self.proxy.sushi_remove(domain, "", "")

	def retrieveServerlist(self):
		return self.proxy.sushi_list("servers","","")
	
	def retrieveServerinfo(self, server):
		map = {}
		domain = "servers/%s" % server
		map["servername"] = server
		map["address"] = self.proxy.sushi_get(domain, "server", "address")
		map["port"] = self.proxy.sushi_get(domain, "server", "port")
		map["name"] = self.proxy.sushi_get(domain, "server", "name")
		map["nick"] = self.proxy.sushi_get(domain, "server", "nick")
		map["nickserv"] = self.proxy.sushi_get(domain, "server", "nickserv")
		map["autoconnect"] = self.proxy.sushi_get(domain, "server", "autoconnect")
		return map


	""" SIGNALS """


	""" SERVER SIGNALS """

	def serverConnect(self, time, server):
		self.addServer(server)
		self.serverPrint(time, server, "Connecting...")

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		self.serverPrint(time, server, "Connected.")

		obj = self.getObject(server)
		obj.setConnected(True)
		self.updateDescription(server,obj=obj)

		self.addChannels(server)
		self.setNick(server, nick)

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		# TODO: clear nicklists of server if existant
		self.addServer(server)
		self.serverPrint(time, server, "Reconnecting to %s" % server)

	# the server is sending a MOTD
	def serverMOTD(self, time, server, message):
		self.serverPrint(time, server, message)

	""" CHANNEL SIGNALS """

	"""
	The topic was set on server "server" in channel "channel" by
	user "nick" to "topic".
	Apply this!
	"""
	def channelTopic(self, time, server, nick, channel, topic):
		
		self.setTopic(time, server, channel, nick, topic)
		
		if not nick:
			return

		if nick == self.getNick(server):
			nick = "You"

		self.channelPrint(time, server, channel, "%s changed the topic to '%s'" % (nick,self.escape(topic)))

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.myPrint("Maki is shutting down!")
		for server in self.getServers():
			self.removeServer(server)
		self.proxy = None

	""" USER SIGNALS """

	"""
	maki says that we are away.
	"""
	def userAway(self, time, server):
		self.setAway(time,server)

	"""
	maki says that we are back from away being.
	"""
	def userBack(self, time, server):
		self.setBack(time,server)

	"""
	The user is away and the server gives us the message he left
	for us to see why he is away and probably when he's back again.
	"""
	def userAwayMessage(self, timestamp, server, nick, message):
		self.channelPrint(timestamp, server, nick, "%s is away: %s" % (nick,message))

	# privmessages are received here
	def userMessage(self, timestamp, server, nick, channel, message):
		color = self.getNickColor(nick)
		message = self.escape(message)
		self.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; %s" % (color,nick,message))

	def ownMessage(self, timestamp, server, channel, message):
		self.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; <msg>%s</msg>" \
		% (self.getColor("ownNick"), self.getNick(server), self.escape(message)))

	def userQuery(self, timestamp, server, nick, message):
		self._simCheck(server,nick)
		self.userMessage(timestamp,server,nick,nick,message)

	def userMode(self, time, server, nick, target, mode, param):
		myNick = self.getNick(server)

		act_color=self.getColor("modeActNick")
		param_color=self.getColor("modeParam")

		actnick = "<font foreground='%s'>%s</font>" % (act_color, self.escape(nick))
		if nick == myNick:
			actnick = "You"

		if target == myNick:
			self.serverPrint(time, server,"%s set <b>%s</b> on you." % (actnick, mode))
		else:
			# if param a user mode is set
			if param:
				nickwrap = "<font foreground='%s'>%s</font>" % (param_color, self.escape(param))
				if param == myNick:
					nickwrap = "You"
				msg = "%s set <b>%s</b> to %s." % (actnick,mode,nickwrap)

				self._prefixMode(server,target,param,mode)
			# else a channel is the target
			else:
				msg = "%s set <b>%s</b> on %s." % (actnick,mode,target)
			self.channelPrint(time, server, target, msg)

	def userCTCP(self, time, server,  nick, target, message):
		pass

	def userNotice(self, time, server, nick, target, message):
		if target == self.getNick(server):
			self._simCheck(server,nick)
			self.userMessage(time, server, nick, nick, message)

	# user sent an /me
	def userAction(self, time, server, nick, channel, action):
		action = self.escape(action)
		self.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, new_nick):
		channel = self.getChannel(server, nick)
		if channel:
			self.renameChannel(server, channel, new_nick)
		
		if nick == self.getNick(server):
			nickwrap = "You are"
			self.setNick(server,self.getNickFromMaki(server))
		else:
			nickwrap = "%s is" % nick
		
		nickchange = "%s now known as %s." % (nickwrap, new_nick)
		nickchange = self.escape(nickchange)

		for channel in self.getChannels(server):
			nicklist = self.getObject(server,channel).getNicklist()
			if nick in nicklist.getNicks() or channel == nick:
				nicklist.modifyNick(nick, new_nick)
				self.channelPrint(time, server, channel, nickchange)

	# user was kicked
	def userKick(self, time, server, nick, channel, who, reason):
		if reason:
			reason = "(%s)" % reason

		if who == self.getNick(server):
			self.getObject(server,channel).setJoined(False)
			self.updateDescription()
			self.channelPrint(time, server, channel, self.escape(\
				"You have been kicked from %s by %s %s" % (channel,nick,reason)))
		else:
			self.channelPrint(time, server, channel, self.escape("%s was kicked from %s by %s %s" % (who,channel,nick,reason)))

	"""
	The user identified by nick quit on the server "server" with
	the reason "reason". "reason" can be empty ("").
	If we are the user all channels were set to joined=False and
	the server's connected-flag is set to False.
	If another user quits on all channels on which the user was on
	a message is generated.
	"""
	def userQuit(self, time, server, nick, reason):
		if nick == self.getNick(server):
			# set the connected flag to False on the server
			obj = self.getObject(server)

			if not obj: # this happens if the tab is closed
				return

			obj.setConnected(False)
			self.updateDescription(server,obj=obj)

			# walk through all channels and set joined = False on them
			channels = self.getChannels(server)
			if not channels:
				return
			for channel in channels:
				obj = self.getObject(server,channel)
				obj.setJoined(False)
				self.updateDescription(server,channel,obj=obj)
		else:
			reasonwrap = ""
			if reason: 
				reasonwrap = " (%s)" % reason

			channels = self.getChannels(server)

			if not channels:
				print "No channels but quit reported.. Hum wtf? o.0"
				return

			# print in all channels where nick joined a message
			for channel in channels:
				obj = self.getObject(server,channel)
				nicklist = obj.getNicklist()

				nicks = nicklist.getNicks() or []

				if nick in nicks or nick == channel:
					nicklist.removeNick(nick)
					self.channelPrint(time, server, channel, \
					"%s has quit%s." % (nick,reasonwrap))
	
	"""
	A user identified by "nick" joins the channel "channel" on 
	server "server.

	If the nick is our we add the channeltab and set properties
	on it, else we generate messages and stuff.
	"""
	def userJoin(self, timestamp, server, nick, channel):
		if nick == self.getNick(server):
			nicks = self.getNicksFromMaki(server,channel)
			topic = self.getTopic(server, channel)

			# returns the iter of the channel if added (ret=0) 
			# or if it's already existent (ret=1) if ret is 0 
			# the nicks and the topic are already applied, else
			# we set them manually.
			ret,iter = self.servertree.addChannel(server, channel, nicks=nicks, topic=topic)

			if not iter:
				print "userJoin(%s,%s,%s): No Server!" % \
					(server,channel,nick)
				return

			obj = self.getObject(server,channel)
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
			
				obj.setTopic(topic)
				obj.setJoined(True)
				self.updateDescription(server,channel,obj=obj)
			else:
				self.__lastLogHack(server,channel,10)

			# fetch the prefixes and apply
			# them to the nicklist of the channel
			# identified by "iter"
			self._prefixFetch(server,channel,nicklist,nicks)

			nickwrap = "You have"
		else:
			nickwrap = "<font foreground='%s'>%s</font> has" % (self.getColor("joinNick"), self.escape(nick))
			self.getObject(server,channel).getNicklist().appendNick(nick)
		self.channelPrint(timestamp, server, channel, "%s joined %s." % (nickwrap, channel))

	# user parted
	def userPart(self, timestamp, server, nick, channel, reason):
		obj = self.getObject(server,channel)
		if not obj:
			return

		if reason: 
			reason = " (%s)" % reason

		if nick == self.getNick(server):
			self.channelPrint(timestamp, server, channel, "You have left %s%s." % (channel,reason))
			
			obj.setJoined(False)
			self.updateDescription(server, channel, obj=obj)

		else:
			obj.getNicklist().removeNick(nick)
			self.channelPrint(timestamp, server, channel, \
			"<font foreground='%s'>%s</font> has left %s%s." % (self.getColor("partNick"), self.escape(nick), self.escape(channel), self.escape(reason)))


	""" COMMAND METHODS """

	# Method to parse the userinput
	def parseCommand(self, command):
		if not command: return
		cmd = command.split(" ")
		if not self.commands.has_key(cmd[0]):
			self.myPrint("Unknown command %s" % cmd[0])
			return
		xargs = None
		if len(cmd)>1:
			xargs = cmd[1:]
		self.commands[cmd[0]](xargs)

	def makiConnect(self, xargs):
		if not xargs:
			self.myPrint("Usage: /connect <servername>")
			return
		self.proxy.connect(xargs[0])

	def makiQuit(self, xargs):
		if not xargs:
			print "global quit"
			list = self.getServers()
			for server in list:
				self.proxy.quit(server,"")
		else:
			reason = ""
			if len(xargs) >= 2:
				reason = " ".join(xargs[1:])
			print "quit local %s" % xargs[0]
			self.proxy.quit(xargs[0], reason)

	def makiNick(self, xargs):
		server = self.getCurrentServer()

		if not self.proxy:
			self.myPrint("No connection to maki.")
			return

		if not xargs:
			self.myPrint("Usage: /nick <new nick>")
			return

		if not server:
			self.myPrint("Can't determine my server.")
			return

		self.proxy.nick(server, xargs[0])

	def makiPart(self, xargs, server=None):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return

		cserver,cchannel = self.getCurrentChannel()
		if not server:
			if not cserver:
				self.myPrint("Could not determine my current server.")
				return
			server = cserver

		channel = ""
		reason = ""

		if not xargs:
			if not cchannel:
				self.myPrint("No channel given.")
				return
			else:
				channel = cchannel
		elif len(xargs) == 1:
			channel = xargs[0]
			reason = ""
		elif len(xargs) >= 2:
			channel = xargs[0]
			reason = " ".join(xargs[1:])
		self.proxy.part(server, channel, reason)

	def makiJoin(self, xargs, server=None):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return
		if not server:
			server = self.getCurrentServer()
			if not server:
				self.myPrint("Can't determine server.")
				return
		if not xargs:
			self.myPrint("Usage: /join <channel> [<key>]")
			return
		key = ""
		if len(xargs) >= 2:
			key = " ".join(xargs[1:])
		self.proxy.join(server,xargs[0],key)

	def makiAction(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return

		if not xargs:
			self.myPrint("Usage: /me <text>")
			return

		server,channel = self.getCurrentChannel()

		if not server or not channel:
			self.myPrint("No channel joined.")
			return

		self.proxy.action(server,channel," ".join(xargs))

	def makiKick(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return

		if not xargs:
			self.myPrint("Usage: /kick <who>")
			return

		server,channel = self.getCurrentChannel()
		if not server:
			self.myPrint("Can't determine server")
			return

		if not channel:
			self.myPrint("You're not on a channel")
			return

		reason = ""
		if len(xargs) >= 2:
			reason = " ".join(xargs[1:])
		self.proxy.kick(server, channel, xargs[0], reason)

	def makiMode(self, xargs):
		if not xargs or len(xargs) < 2:
			self.myPrint("Usage: /mode <target> (+|-)<mode> [param]")
			return
		server = self.getCurrentServer()
		if not server:
			self.myPrint("could not determine server.")
			return
		param = ""
		if len(xargs)==3:
			param = xargs[2]
		self.proxy.mode(server, xargs[0], "%s %s" % (xargs[1],param))

	def makiTopic(self, xargs):
		if not xargs:
			self.myPrint("Usage: /topic <topic text>")
			return
		else:
			topic = " ".join(xargs)

		server,channel = self.getCurrentChannel()

		if not server or not channel:
			self.myPrint("Where should i set the topic?")
			return

		return self.proxy.topic(server, channel, topic)

	def makiAway(self, xargs):
		if not xargs:
			self.makiBack(xargs)
			return

		s = self.getCurrentServer()
		if not s:
			self.myPrint("Can't determine server.")
			return

		self.proxy.away(s," ".join(xargs))

	def makiBack(self, xargs):
		s = self.getCurrentServer()
		if not s:
			self.myPrint("Can't determine server.")
			return
		self.proxy.back(s)

	def makiOper(self, xargs):
		pass

	def makiKill(self, xargs):
		pass

	def makiShutdown(self, w):
		if self.proxy:
			self.proxy.shutdown()
			self.myPrint("Maki shutted down.")
			for server in self.getServers():
				print "removing %s" % server
				self.removeServer(server)

	""" TEKKA USER COMMANDS """

	def tekkaQuery(self, xargs):
		if not xargs:
			self.myPrint("Usage: /query <nick>")
			return
		server, channel = self.getCurrentChannel()
		if not server:
			self.myPrint("query who on which server?")
			return
		if not self.getChannel(server,xargs[0],sens=False):
			self.addChannel(server, xargs[0])

	def tekkaClear(self, xargs):
		pass

	""" HELPER """

	def __lastLogHack(self, server, channel, lines):
		obj = self.getObject(server,channel)
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
			buffer.insert_html(buffer.get_end_iter(), "<font foreground=\"#DDDDDD\">%s</font>" % self.escape(line))


	"""
	solution to set the prefixes in the nicklist of a new
	added server. The iter returned by addChannel() is
	passed to this function (chaniter) like the nicks
	and prefixes for the nicks were fetched and added to
	the channel-nicklist
	"""
	def _prefixFetch(self, server, channel, nicklist, nicks):
		for nick in nicks:
			prefix = self.userChannelPrefix(server,channel,nick)
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
		check = self.getChannel(server, nick)
		if not check:
			simfound = False
			for schannel in self.getChannels(server):
				if schannel.lower() == nick.lower():
					self.renameChannel(server, schannel, nick)
					simfound = True
			if not simfound:
				self.addChannel(server,nick)

	"""
	checks if the mode is a prefix-mode. if a prefix mode is
	given the prefix-char is added.
	"""
	def _prefixMode(self, server, channel, nick, mode):
		if mode[1] not in ("q","a","o","h","v"):
			return
		nicklist = self.getObject(server,channel).getNicklist()
		if not nicklist:
			return
		nicklist.setPrefix(nick, self.userChannelPrefix(server,channel,nick))



	""" PLACEHOLDER TO OVERLOAD """

	def getNickColor(self, nick):
		colors = self.getNickColors()
		if not colors:
			return "#2222AA"
		return colors[ord(nick[0])%len(colors)]

	# escapes all incoming strings
	def escape(self, str):
		pass

	# prints the string "string" to the channel output of channel "channel"
	# on server "server"
	def channelPrint(self, timestamp, server, channel, string):
		print "%s@%s: %s" % (channel, server, string)

	# prints the string "string" to the server output of "server"
	def serverPrint(self, server, string):
		print "%s: %s" % (server,string)

	# prints the string "string" to the current output
	def myPrint(self, string, html=False):
		print string

	def quit(self):
		return

	def setTopic(self, time, server, channel, nick, topic):
		pass

	# set away status on server "server"
	def setAway(self, time, server):
		pass

	# unset away status on server "server"
	def setBack(self, time, server):
		pass

	# updates the server or channel description
	def updateDescription(server=None, channel=None, obj=None):
		pass

	# return a server or (if channel is given) a channel object
	def getObject(self, server, channel=None):
		pass

	# return a list of all servers maki is connected to
	def getServers(self):
		pass

	# return a list of all channels maki joined on server "server"
	def getChannels(self, server):
		pass

	def getRow(self, server, channel=None):
		pass

	def getChannel(self, server, channel,sens=True):
		pass

	def getCurrentServer(self):
		pass

	def getCurrentChannel(self):
		pass

	def getCurrentRow(self):
		pass

	def addServer(self, server):
		pass

	def addChannel(self, server, channel, nicks=[], topic="", topicsetter=""):
		pass

	def removeServer(self, server):
		pass

	def removeChannel(self, server, channel):
		pass

	def renameChannel(self, server, channel, newName):
		pass

if __name__ == "__main__":
	print "testing"
	test = tekkaCom()
