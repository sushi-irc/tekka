import sys
import dbus
from dbus.mainloop.glib import DBusGMainLoop

import time
"""

Rausfinden auf welchem Server wir senden
Rausfinden auf welchem Channel wir senden
Rausfinden was wir senden wollen


"""

class tekkaCom(object):
	def __init__(self):
		dbus_loop = DBusGMainLoop()
		self.bus = dbus.SessionBus(mainloop=dbus_loop)
		self.proxy = None
		try:
			self.proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
		except dbus.exceptions.DBusException, e:
			print e
			print "Is maki running?"
			if not self.proxy:
				sys.exit(1)
		if self.proxy:
			self.bus.add_signal_receiver(self.readText, "message", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userPart, "part", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userJoin, "join", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userQuit, "quit", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userKick, "kick", dbus_interface="de.ikkoku.sushi")
			self.bus.add_signal_receiver(self.userNick, "nick", dbus_interface="de.ikkoku.sushi")

		self.commands = { 
			"nick" : self.makiNick,
			"part" : self.makiPart,
			"join" : self.makiJoin,
			"me"   : self.makiAction,
			"kick" : self.makiKick,
			"mode" : self.makiMode,
			"topic": self.makiTopic,
			"quit" : self.makiQuit,
		"usermode" : self.makiUsermode,
			"ctcp" : self.tekkaCTCP,
			"dcc"  : self.tekkaDCC
		}


	def readText(self, timestamp, server, channel, nick, message):
		self.channelPrint(server, channel, "<%s> %s" % (nick, message))

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
					self.proxy.say(server,channel,text)

	def channelPrint(self, server, channel, string):
		print "%s@%s: %s" % (channel, server, string)

	def serverPrint(self, server, string):
		print "%s: %s" % (server,string)

	def myPrint(self, string):
		print string

	def quit(self):
		return

	def addServers(self):
		servers = self.proxy.servers()
		if not servers:
			return
		for server in servers:
			# addServer in tekkaMain
			self.addServer(server)
			self.addChannels(server)

	def addChannels(self, server):
		channels = self.proxy.channels(server)
		print channels
		for channel in channels:
			print "got channel: %s" % channel
			self.addChannel(server, channel)

	def userNick(self, time, server, nick, new_nick):
		nickchange = "%s is now known as %s." % (nick, new_nick)
		self.serverPrint(server, nickchange)
		"""
		else:
			for channel in self.getChannels(server):
				nickiter = findNick(server, channel, nick)
				if nickiter:
					self.channelPrint(server, channel, nickchange)
					nickiter.magicdostuff()
		"""
	def userKick(self, time, server, channel, nick, who):
		self.channelPrint(server, channel, "%s was kicked from %s by %s" % (who,channel,nick))

	def userQuit(self, time, server, nick):
		channels = self.getChannels(server)
		if not channels:
			return
		for channel in channels:
			self.channelPrint(server, channel, "%s has quit." % nick)
	
	def userJoin(self, timestamp, server, channel, nick):
		self.channelPrint(server, channel, "%s has joined %s." % (nick, channel))

	def userPart(self, timestamp, server, channel, nick):
		self.channelPrint(server, channel, "%s has left %s." % (nick, channel))

	def connectServer(self, widget):
		print "would connect"

	def newServer(self, newServer):
		print "adding new server to maki"

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

	def makiQuit(self, xargs):
		if not xargs:
			list = self.getServers()
			for server in list:
				self.proxy.quit(server)
			self.quit()
		else:
			self.proxy.quit(xargs)

	def makiNick(self, xargs):
		return

	def makiPart(self, xargs):
		if not self.proxy:
			self.myPrint("No connection to maki.")
			return
		server,channel = self.getCurrentChannel()
		if not server:
			self.myPrint("Could not determine my current server.")
			return
		if xargs and len(xargs) == 1:
			self.proxy.part(server, xargs[0])
			self.removeChannel(server, xargs[0])
		else:
			if channel:
				self.proxy.part(server, channel)
				self.removeChannel(server, channel)
			else:
				self.myPrint("No channel given for /part")

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
		self.proxy.join(server,xargs[0])
		self.addChannel(server,xargs[0])


	def makiAction(self, xargs):
		return

	def makiKick(self, xargs):
		return

	def makiMode(self, xargs):
		return

	def makiTopic(self, xargs):
		if not xargs or len(xargs) == 0:
			topic = ""
		else:
			topic = xargs.join(" ")
		server,channel = getCurrentChannel()
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

	def tekkaCTCP(self, xargs):
		return

	def tekkaDCC(self, xargs):
		return

