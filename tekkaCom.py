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
		"usermode" : self.makiUsermode,
			"query": self.tekkaQuery,
			"clear": self.tekkaClear,
			"ctcp" : self.tekkaCTCP,
			"dcc"  : self.tekkaDCC
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

		# setup signals
		if self.proxy:
			# Message-Signals
			self.bus.add_signal_receiver(self.userMessage, "message", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.ownMessage, "own_message", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.ownQuery, "own_query", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userQuery, "query", dbus_interface="de.ikkoku.sushi")

			self.bus.add_signal_receiver(self.userPart, "part", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userJoin, "join", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userQuit, "quit", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userKick, "kick", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userNick, "nick", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userAction, "action", dbus_interface="de.ikkoku.sushi")
			#self.bus.add_signal_receiver(self.userAway, "away", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userAwayMessage, "away_message", dbus_interface="de.ikkoku.sushi")
			#self.bus.add_signal_receiver(self.userBack, "back", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userCTCP, "ctcp", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userNotice, "notice", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userMode, "mode", dbus_interface="de.ikkoku.sushi")

			# Server-Signals
			self.bus.add_signal_receiver(self.serverConnect, "connect", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverConnected, "connected", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverReconnect, "reconnect", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverMOTD, "motd", dbus_interface="de.ikkoku.sushi")

			# Channel-Signals
			self.bus.add_signal_receiver(self.channelTopic, "topic", dbus_interface="de.ikkoku.sushi")

			# Maki signals
			self.bus.add_signal_receiver(self.makiShutdownSignal, "shutdown", dbus_interface="de.ikkoku.sushi")

	

	# signal connected to the gtk.entry
	def sendText(self, widget):
		print "text received from widget"
		
		text = widget.get_text()
		if not text:
			return
		widget.set_text("")

		if text[0] == "/" and text[1] != "/":
			self.parseCommand(text[1:])
		else:
			if self.proxy:
				server,channel = self.servertree.getCurrentChannel()
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
			self.servertree.addServer(server)
			self.addChannels(server)
			self.setNick(server, self.getNickFromMaki(server))

	def addChannels(self, server):
		channels = self.proxy.channels(server)
		
		for channel in channels:
			nicks = self.getNicksFromMaki(server, channel)

			iter,output = self.servertree.addChannel(server, channel, nicks=nicks, \
			topic=[self.getTopic(server,channel),""])

			if not iter:
				continue

			self._iterPrefixFetch(server,iter,nicks)
	
	def getTopic(self, server, channel):
		return self.proxy.topic(server,channel,"")

	def userChannelPrefix(self, server, channel, nick):
		if not self.proxy: return ""
		return self.proxy.user_channel_prefix(server,channel,nick) 

	# solution to set the prefixes in the nicklist of a new
	# added server. The iter returned by addChannel() is
	# passed to this function (chaniter) like the nicks
	# and prefixes for the nicks were fetched and added to
	# the channel-nicklist
	def _iterPrefixFetch(self, server, chaniter, nicks):
		if not chaniter: 
			return
		model = self.servertree.get_model()
		channel = model.get(chaniter, self.servertree.COLUMN_NAME)
		nicklist = model.get(chaniter,self.servertree.COLUMN_NICKLIST)
		if channel:
			channel = channel[0]
		if nicklist:
			nicklist = nicklist[0]

		for nick in nicks:
			prefix = self.userChannelPrefix(server,channel,nick)
			if not prefix: 
				continue
			nicklist.setPrefix(nick, prefix)

	# checks if the mode is a prefix-mode. if a prefix mode is
	# given the prefix-char is added.
	def _prefixMode(self, server, channel, nick, mode):
		if mode[1] not in ("q","a","o","h","v"):
			return
		row = self.servertree.getRow(server,channel)
		if not row and len(row) != 2:
			return
		nicklist = row[1][self.servertree.COLUMN_NICKLIST]
		if not nicklist:
			return
		nicklist.setPrefix(nick, self.userChannelPrefix(server,channel,nick))


	""" SERVER CREATION """

	def createServer(self, smap):
		domain = "servers/%s" % smap["servername"]
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
		self.servertree.addServer(server)
		self.serverPrint(time, server, "Connecting...")

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		self.addChannels(server)
		self.setNick(server, nick)

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		self.servertree.addServer(server)
		self.serverPrint(time, server, "Reconnecting to %s" % server)

	# the server is sending a MOTD
	def serverMOTD(self, time, server, message):
		self.serverPrint(time, server, message, raw=True)

	""" CHANNEL SIGNALS """

	def channelTopic(self, time, server, nick, channel, topic):
		self.servertree.setTopic(server,channel,topic,nick)
		self.setTopicInBar(server,channel)
		if not nick: return
		nickwrap = nick
		if nick == self.getNick(server):
			nickwrap = "You"
		self.channelPrint(time, server, channel, "%s changed the topic to '%s'" % (nickwrap,self.escapeHTML(topic)))

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.myPrint("Maki is shutting down!")
		for server in self.servertree.getServers():
			self.servertree.removeServer(server)
		self.proxy = None

	""" USER SIGNALS """

	def userAwayMessage(self, timestamp, server, nick, message):
		self.servertree.channelPrint(timestamp, server, nick, "%s is away: %s" % (nick,message))

	# privmessages are received here
	def userMessage(self, timestamp, server, nick, channel, message):
		color = self.getColor("nick")
		message = self.escapeHTML(message)
		self.channelPrint(timestamp, server, channel, \
		"&lt;<font foreground='%s'>%s</font>&gt; <msg>%s</msg>" % (color,nick,message))

	def ownMessage(self, timestamp, server, channel, message):
		self.channelPrint(timestamp, server, channel, "&lt;<font foreground='%s'>%s</font>&gt; <msg>%s</msg>" \
		% (self.getColor("ownNick"), self.getNick(server), self.escapeHTML(message)))
	
	def ownQuery(self, timestamp, server, channel, message):
		self.ownMessage(timestamp,server,channel,message)
	
	def userQuery(self, timestamp, server, nick, message):
		check = self.servertree.getChannel(server,nick)
		if not check:
			simfound=0
			for schannel in self.servertree.getChannels(server):
				if schannel.lower() == nick.lower():
					self.servertree.renameChannel(server, schannel, nick)
					simfound=1
			if not simfound:
				self.servertree.addChannel(server,nick)
		self.userMessage(timestamp,server,nick,nick,message)

	def userMode(self, time, server, nick, target, mode, param):
		myNick = self.getNick(server)

		act_color=self.getColor("modeActNick")
		param_color=self.getColor("modeParam")

		actnick = "<font foreground='%s'>%s</font>" % (act_color, self.escapeHTML(nick))
		if nick == myNick:
			actnick = "You"

		if target == myNick:
			self.myPrint("%s set <b>%s</b> on you." % (actnick, mode))
		else:
			# if param a user mode is set
			if param:
				nickwrap = "<font foreground='%s'>%s</font>" % (param_color, self.escapeHTML(param))
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
		pass

	# user sent an /me
	def userAction(self, time, server, nick, channel, action):
		action = self.escapeHTML(action)
		self.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, new_nick):
		channel =  self.servertree.getChannel(server, nick)
		if channel:
			self.servertree.renameChannel(server, channel, new_nick)
		
		if nick == self.getNick(server):
			nickwrap = "You are"
			self.setNick(server,self.getNickFromMaki(server))
		else:
			nickwrap = "%s is" % nick
		
		nickchange = "%s now known as %s." % (nickwrap, new_nick)
		nickchange = self.escapeHTML(nickchange)

		for row in self.servertree.getChannels(server,row=True):
			channel = row[self.servertree.COLUMN_NAME]
			nicklist = row[self.servertree.COLUMN_NICKLIST]
			if nick in nicklist.getNicks() or channel == nick:
				nicklist.modifyNick(nick, new_nick)
				self.channelPrint(time, server, channel, nickchange)

	# user was kicked
	def userKick(self, time, server, nick, channel, who, reason):
		if reason:
			reason = "(%s)" % reason

		if who == self.getNick(server):
			self.servertree.channelDescription(server, channel, "("+channel+")")
			self.channelPrint(time, server, channel, self.escapeHTML("You have been kicked from %s by %s %s" % (channel,nick,reason)))
		else:
			self.channelPrint(time, server, channel, self.escapeHTML("%s was kicked from %s by %s %s" % (who,channel,nick,reason)))

	# user has quit
	def userQuit(self, time, server, nick, reason):
		if nick == self.getNick(server):
			self.servertree.serverDescription(server, "("+server+")")
			channels = self.servertree.getChannels(server)
			if not channels: 
				return
			for channel in channels:
				self.servertree.channelDescription(server, channel, "("+channel+")")
		else:
			reasonwrap = ""
			if reason: 
				reasonwrap = " (%s)" % reason

			channels = self.servertree.getChannels(server,row=True)

			if not channels:
				print "No channels but quit reported.. Hum wtf? o.0"
				return

			# print in all channels where nick joined a message
			for channel in channels:
				channelname = channel[self.servertree.COLUMN_NAME]
				nicklist = channel[self.servertree.COLUMN_NICKLIST]

				nicks = nicklist.getNicks() or []

				if nick in nicks or nick == channel:
					nicklist.removeNick(nick)
					self.channelPrint(time, server, channelname, "%s has quit%s." % (nick,reasonwrap))
	
	# user joined
	def userJoin(self, timestamp, server, nick, channel):
		if nick == self.getNick(server):
			nicks = self.getNicksFromMaki(server,channel)
			iter,output = self.servertree.addChannel(server, channel, nicks=nicks)
			self._iterPrefixFetch(server,iter,nicks)
			nickwrap = "You"
		else:
			nickwrap = "<font foreground='%s'>%s</font>" % (self.getColor("joinNick"), self.escapeHTML(nick))
			srow,crow = self.servertree.getRow(server,channel)
			if crow: crow[2].appendNick(nick)
		self.channelPrint(timestamp, server, channel, "%s have joined %s." % (nickwrap, channel))

	# user parted
	def userPart(self, timestamp, server, nick, channel, reason):

		if nick == self.getNick(server):
			rwrap = ""
			if reason:
				rwrap = " (%s)" % reason
			self.channelPrint(timestamp, server, channel, "You have left %s%s." % (channel,rwrap))

			# FIXME: QND
			self.servertree.channelDescription(server, channel, "("+channel+")")
			return

		if reason: reason = " (%s)" % reason
		srow,crow = self.servertree.getRow(server,channel)
		if crow: crow[2].removeNick(nick)
		self.channelPrint(timestamp, server, channel, "<font foreground='%s'>%s</font> has left %s%s." % (self.getColor("partNick"), nick, channel,reason))



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
			list = self.servertree.getServers()
			for server in list:
				self.proxy.quit(server,"")
			self.quit()
		else:
			reason = ""
			if len(xargs) >= 2:
				reason = " ".join(xargs[1:])
			print "quit local %s" % xargs[0]
			self.proxy.quit(xargs[0], reason)
			self.servertree.removeServer(xargs[0])

	def makiNick(self, xargs):
		server = self.servertree.getCurrentServer()
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
		cserver,cchannel = self.servertree.getCurrentChannel()
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
			server = self.servertree.getCurrentServer()
			if not server:
				self.myPrint("Can't determine server.")
				return
		if not xargs:
			self.myPrint("Where you want to join to?")
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
		server,channel = self.servertree.getCurrentChannel()
		if not server or not channel:
			self.myPrint("No channel joined.")
		self.proxy.action(server,channel," ".join(xargs))

	def makiKick(self, xargs):
		if not self.proxy:
			return
		if not xargs:
			self.myPrint("Usage: /kick <who>")
			return
		server,channel = self.servertree.getCurrentChannel()
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
		return

	def makiTopic(self, xargs):
		if not xargs or len(xargs) == 0:
			topic = ""
		else:
			topic = " ".join(xargs)
		server,channel = self.servertree.getCurrentChannel()
		if not server or not channel:
			return
		return self.proxy.topic(server, channel, topic)

	def makiUsermode(self, xargs):
		return

	def makiShutdown(self, w):
		if self.proxy:
			self.proxy.shutdown()
			self.myPrint("Maki shutted down.")
			for server in self.getServers():
				print "removing %s" % server
				self.servertree.removeServer(server)

	""" TEKKA USER COMMANDS """

	def tekkaQuery(self, xargs):
		if not xargs:
			self.myPrint("Usage: /query <nick>")
			return
		server, channel = self.servertree.getCurrentChannel()
		if not server:
			self.myPrint("query who on which server?")
			return
		if not self.servertree.getChannel(server,xargs[0],sens=False):
			self.servertree.addChannel(server, xargs[0])

	def tekkaClear(self, xargs):
		pass

	def tekkaCTCP(self, xargs):
		return

	def tekkaDCC(self, xargs):
		return


	""" PLACEHOLDER TO OVERLOAD """


	def channelPrint(self, timestamp, server, channel, string):
		print "%s@%s: %s" % (channel, server, string)

	def serverPrint(self, server, string):
		print "%s: %s" % (server,string)

	def myPrint(self, string):
		print string

	def quit(self):
		return

if __name__ == "__main__":
	print "testing"
	test = tekkaCom()
