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
			self.bus.add_signal_receiver(self.readText, "message", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userPart, "part", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userJoin, "join", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userQuit, "quit", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userKick, "kick", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userNick, "nick", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userAction, "action", dbus_interface="de.ikkoku.sushi")
			#self.bus.add_signal_receiver(self.userAway, "away", dbus_interface="de.ikkoku.sushi")
			#self.bus.add_signal_receiver(self.userBack, "back", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userCTCP, "ctcp", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userNotice, "notice", dbus_interface="de.ikkoku.sushi")

			# Server-Signals
			self.bus.add_signal_receiver(self.serverConnect, "connect", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverConnected, "connected", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverReconnect, "reconnect", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.serverMOTD, "motd", dbus_interface="de.ikkoku.sushi")

			# Maki signals
			self.bus.add_signal_receiver(self.makiShutdownSignal, "shutdown", dbus_interface="de.ikkoku.sushi")


	# privmessages are received here
	def readText(self, timestamp, server, channel, nick, message):
		self.channelPrint(timestamp, server, channel, "<%s> %s" % (nick,message), nick=nick)

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
				server,channel = self.getCurrentChannel()
				if not server:
					self.myPrint("could not determine server.")
					return
				if not channel:
					self.myPrint("would send to server directly.")
				else:
					if text[0:2] == "//":
						text = text[1:]
					self.proxy.say(server,channel,text)



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

	def addChannels(self, server):
		channels = self.proxy.channels(server)
		print channels
		for channel in channels:
			print "got channel: %s" % channel
			self.addChannel(server, channel)


	""" SIGNALS """


	""" SERVER SIGNALS """

	def serverConnect(self, time, server):
		self.addServer(server)
		self.serverPrint(time, server, "Connecting...")

	# maki connected to a server
	def serverConnected(self, time, server, nick):
		self.setNick(server, nick)

	# maki is reconnecting to a server
	def serverReconnect(self, time, server):
		self.serverPrint(time, server, "Reconnecting to %s" % server)

	# the server is sending a MOTD
	def serverMOTD(self, time, server, message):
		self.serverPrint(time, server, "Message of the Day:\n%s" % message)

	""" MAKI SIGNALS """

	def makiShutdownSignal(self, time):
		self.myPrint("Maki is shutting down!")
		for server in self.getServers():
			self.removeServer(server)
		self.proxy = None

	""" USER SIGNALS """

	def userCTCP(self, time, server, target, nick, message):
		pass

	def userNotice(self, time, server, target, nick, message):
		pass

	# user sent an /me
	def userAction(self, time, server, channel, nick, action):
		self.channelPrint(time, server, channel, "%s %s" % (nick,action))

	# user changed his nick
	def userNick(self, time, server, nick, new_nick):
		channel =  self.getChannel(server, nick)
		if channel:
			self.renameChannel(server, channel, new_nick)
		
		if nick == self.getNick(server):
			nickwrap = "You are"
			self.setNick(server,self.getNickFromMaki(server))
		else:
			nickwrap = "%s is" % nick
		
		nickchange = "%s now known as %s." % (nickwrap, new_nick)
		for channel in self.getChannels(server):
			if nick in self.getNicksFromMaki(server,channel) or channel == nick:
				self.channelPrint(time, server, channel, nickchange)

	# user was kicked
	def userKick(self, time, server, channel, nick, who, reason):
		if reason:
			reason = "(%s)" % reason
		self.channelPrint(time, server, channel, "%s was kicked from %s by %s %s" % (who,channel,nick,reason))

	# user has quit
	def userQuit(self, time, server, nick, reason):
		print "userquit"
		if nick == self.getNick(server):
			self.removeServer(server)
		else:
			if reason: reason = " (%s)" % reason
			channels = self.getChannels(server)
			if not channels:
				return
			for channel in channels:
				if nick in self.getNicksFromMaki(server,channel) or nick == channel:
					self.channelPrint(time, server, channel, "%s has quit%s." % (nick,reason))
	
	# user joined
	def userJoin(self, timestamp, server, channel, nick):
		if nick == self.getNick(server):
			self.addChannel(server, channel)
			nickwrap = "You"
		else:
			nickwrap = nick
		self.channelPrint(timestamp, server, channel, "%s joined %s." % (nickwrap, channel))

	# user parted
	def userPart(self, timestamp, server, channel, nick, reason):
		if nick == self.getNick(server):
			self.removeChannel(server,channel)
			return
		if reason: reason = " (%s)" % reason
		self.channelPrint(timestamp, server, channel, "%s left %s%s." % (nick, channel,reason))



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
				self.proxy.quit(server)
			self.quit()
		else:
			reason = ""
			if len(xargs) >= 2:
				reason = " ".join(xargs[1:])
			print "quit local %s" % xargs[0]
			self.proxy.quit(xargs[0], reason)
			self.removeServer(xargs[0])

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

	def makiPart(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return
		server,cchannel = self.getCurrentChannel()
		if not server:
			self.myPrint("Could not determine my current server.")
			return

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
		self.removeChannel(server,channel)

	def makiJoin(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return
		server = self.getCurrentServer()
		if not server:
			self.myPrint("Can't determine server.")
			return
		if not xargs:
			self.myPrint("Where you want to join to?")
			return
		key = ""
		if len(xargs) == 2:
			key = xargs[1]
		self.proxy.join(server,xargs[0],key)
		self.addChannel(server,xargs[0])


	def makiAction(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return
		if not xargs:
			self.myPrint("Usage: /me <text>")
		server,channel = self.getCurrentChannel()
		if not server or not channel:
			self.myPrint("No channel joined.")
		self.proxy.action(server,channel," ".join(xargs))

	def makiKick(self, xargs):
		if not self.proxy:
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
		return

	def makiTopic(self, xargs):
		if not xargs or len(xargs) == 0:
			topic = ""
		else:
			topic = " ".join(xargs)
		server,channel = self.getCurrentChannel()
		if not server or not channel:
			return
		self.proxy.topic(server, channel, topic)

	def makiUsermode(self, xargs):
		return

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
