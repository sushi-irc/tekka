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
		widget.set_text("")

		if text[0] == "/" and text[1] != "/":
			self.parseCommand(text[1:])
		else:
			if self.proxy:
				server = self.getCurrentServer()
				if not server:
					self.myPrint("can't determine server.")
					return
				channel = self.getCurrentChannel(server)
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
			print channel
			self.addChannel(server, channel)

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
			self.myPrint("no connection to maki.")
			return
		server = self.getCurrentServer()
		if not server:
			self.myPrint("could not determine my current server.")
			return
		if xargs and len(xargs) == 1:
			self.proxy.part(server, xargs[0])
			self.removeChannel(server, xargs[0])
		else:
			channel = self.getCurrentChannel(server)
			if channel:
				self.proxy.part(server, channel)
				self.removeChannel(server, channel)

	def makiJoin(self, xargs):
		if not self.proxy:
			self.myPrint("no connection to maki.")
			return
		server = self.getCurrentServer()
		if not server:
			self.myPrint("can't determine server.")
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
		return

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

