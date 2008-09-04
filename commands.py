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

import time

config = None
gui = None
com = None

commands = {}

def parseInput(text):
	"""
		TODO: document
	"""
	if not text:
		return

	serverTab,channelTab = gui.tabs.getCurrentTabs()

	if text[:2]=="//" or text[0] != "/":
		if not channelTab:
			return
		com.sendMessage(serverTab.name, channelTab.name, text)

	else:
		list = text[1:].split(" ")
		cmd = list[0]

		if not commands.has_key(cmd):
			gui.myPrint("Unknown command '%s'; Forwarding raw." % (cmd))
			com.raw(serverTab.name, cmd.upper() + " ".join(list[1:]))

		else:
			commands[cmd](serverTab, channelTab, list[1:])

def makiConnect(currentServer, currentChannel, args):
	"""
		Connect to server args[0]
	"""
	if not args:
		return gui.myPrint("Usage: /connect <servername>")

	com.connectServer(args[0])

def makiQuit(currentServer, currentChannel, args):
	"""
		Quit from server args[0] or
		- if no args given - quit the
		current server.
	"""

	if not currentServer:
		return gui.myPrint("makiQuit: Could not determine server.")

	reason = " ".join(args)

	com.quitServer(currentServer.name, reason)

def makiNick(currentServer, currentChannel, args):
	"""
		Change the nick on the current server
		to args[0].
	"""
	if not args:
		return gui.myPrint("Usage: /nick <new nick>")

	if not currentServer:
		return gui.myPrint("Can't determine my server.")

	com.nick(currentServer.name, args[0])

def makiPart(currentServer, currentChannel, args):
	"""
		Part the channel args[0] with the reason in args[1:] (optional).
		If no args are given, part the current channel
		with the standard part reason.
	"""
	if not currentServer:
		return gui.myPrint("Could not determine server.")

	if not currentChannel and not args:
		return gui.myPrint("No channel active.")

	elif args:
		channel = args[0]

	elif currentChannel:
		channel = currentChannel.name

	reason = " ".join(args)[1:]
	self.com.part(currentServer.name, channel, reason)


def makiJoin(currentServer, currentChannel, args):
	"""
		Joins the channel args[0].
		If given, args[1] is used as key.
	"""
	if not currentServer:
		return gui.myPrint("Can't determine server.")

	if not args:
		return gui.myPrint("Usage: /join <channel> [<key>]")
	
	key = " ".join(args[1:])
	com.join(currentServer.name, args[0], key)

def makiAction(currentServer, currentChannel, args):
	"""
		does a ACTION command with all arguments joined together.
	"""
	if not args:
		return gui.myPrint("Usage: /me <text>")

	if not currentChannel:
		return gui.myPrint("Can't find active channel.")

	com.action(currentServer.name, currentChannel.name, " ".join(args))

# XXX XXX XXX XXX XXX XXX XXX WARNING XXX XXX XXX XXX XXX XXX XXX #

def makiKick(self, args):
	"""
		Kick the user args[0] from current channel.
	"""
	if not args:
		return gui.myPrint("Usage: /kick <who>")

	serverTab, channelTab = gui.tabs.getCurrentTabs()

	if not channelTab:
		return gui.myPrint("You're not on a channel")
	
	reason = " ".join(args[1:])
	self.com.kick(serverTab.name, channelTab.name, args[0], reason)

# XXX XXX XXX XXX XXX #
#          .          #
#         / \         #
#        / _ \        #
#       / | | \       #
#      /  |_|  \      #
#     /         \     #
#    /     O     \    #
#   '-------------'   #
# WATCH YOUR STEP:    #
# buggy code          #
# XXX XXX XXX XXX XXX #

def makiMode(currentServer, currentChannel, args):

	if not args or len(args) < 2:
		return gui.myPrint("Usage: /mode <target> (+|-)<mode> [param]")

	if not currentServer:
		return gui.myPrint("Could not determine server.")

	if len(args) > 2:
		# a parameter is given
		param = " ".join(args[2:])

	com.mode(currentServer.name, args[0], "%s %s" % (args[1],param))

def makiTopic(self, xargs):
	if not xargs:
		self.myPrint("Usage: /topic <topic text>")
		return
	else:
		topic = " ".join(xargs)

	server,channel = self.gui.serverTree.getCurrentChannel()

	if not server or not channel:
		self.myPrint("Where should i set the topic?")
		return

	return self.com.setTopic(server, channel, topic)

def makiAway(self, xargs):
	if not xargs:
		self.makiBack(xargs)
		return

	s = self.gui.serverTree.getCurrentServer()
	if not s:
		self.myPrint("Can't determine server.")
		return

	self.com.setAway(s," ".join(xargs))

def makiBack(self, xargs):
	s = self.gui.serverTree.getCurrentServer()
	if not s:
		self.gui.myPrint("Can't determine server.")
		return
	self.com.setBack(s)

def makiNickserv(self, xargs):
	server = self.gui.serverTree.getCurrentServer()

	if not server:
		self.gui.myPrint("Can't determine server.")
		return

	self.com.nickserv(server)

def makiCTCP(self, xargs):
	if not xargs or len(xargs) < 2:
		self.gui.myPrint("Usage: /ctcp <target> <message>")
		return
	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return
	self.com.ctcp(server, xargs[0], xargs[1])

def makiNotice(self, xargs):
	if not xargs or len(xargs) < 2:
		self.gui.myPrint("Usage: /notice <target> <message>")
		return

	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	self.com.notice(server, xargs[0], " ".join(xargs[1:]))

def makiMessage(self, xargs):
	if not xargs or len(xargs) < 2:
		self.gui.myPrint("Usage: /msg <nick> <message>")

	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	# to prevent recursion disable command parsing here
	self.sendMessage(server, xargs[0], " ".join(xargs[1:]), parse_cmd=False)

def makiOper(self, xargs):
	if not xargs or len(xargs) < 2:
		self.gui.myPrint("Usage: /oper <user> <pass>")
		return

	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	self.com.oper(server, xargs[0], " ".join(xargs[1:]))

def makiKill(self, xargs):
	if not xargs or len(xargs) < 2:
		self.gui.myPrint("Usage: /kill <user> <reason>")
		return

	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	self.com.kill(server, xargs[0], xargs[1])

def makiList(self, xargs):
	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	try:
		channel = xargs[0]
	except:
		channel = ""
	self.gui.serverPrint(time.time(), server, "Start of list.")
	self.com.list(server, channel)

def makiRaw(self, xargs):
	if not xargs or len(xargs) < 1:
		self.gui.myPrint("Usage: /raw <command>")
		return

	server = self.gui.serverTree.getCurrentServer()
	if not server:
		self.gui.myPrint("Could not determine server.")
		return

	xargs[0] = xargs[0].upper()
	self.com.raw(server, " ".join(xargs))

def makiWhois(currentServer, currentChannel, args):
	"""
		/whois <mask> on current server
	"""
	if not args:
		return gui.myPrint("No server activated.")
	
	com.sushi.whois(currentServer.name, args[0])

""" TEKKA USER COMMANDS """

def tekkaQuery(self, xargs):
	"""
	Opens a new channel tab for xargs[0] (usually a nick)
	"""
	if not xargs:
		return self.myPrint("Usage: /query <nick>")

	server = self.gui.serverTree.getCurrentServer()

	if not server:
		return self.myPrint("query who on which server?")

	nick = xargs[0]

	if not self.gui.serverTree.getInCaseChannel(server, nick):
		tab = self.gui.createQuery(server, nick)
		self.gui.serverTree.addTab(tab)

		output = tab.buffer

		for line in self.com.fetchLog(server, channel.lower(), self.com.getConfig().lastLogLines):
			output.insertHTML(output.get_end_iter(), \
				"<font foreground='#DDDDDD'>%s</font>" % \
					self.gui.escape(line))

def tekkaClear(self, xargs):
	s,c = self.gui.serverTree.getCurrentChannel()
	
	if not c:
		s[self.gui.serverTree.COLUMN_OBJECT].output.clear()
	else:
		s[self.gui.serverTree.COLUMN_OBJECT].output.clear()


def setup(_config, _gui, _com):
	"""
		Setup the command module.
		  * Set modules
		  * Set command mapping
	"""
	global config, gui, com, commands

	config = _config
	gui = _gui
	com = _com

	commands = {
		"connect" : makiConnect,
		"nick" : makiNick,
		"part" : makiPart,
		"join" : makiJoin,
			"j" : makiJoin,
		"me"   : makiAction,
		"kick" : makiKick,
		"mode" : makiMode,
		"topic": makiTopic,
		"quit" : makiQuit,
		"away" : makiAway,
		"back" : makiBack,
	"nickserv" : makiNickserv,
		"ctcp" : makiCTCP,
		"notice" : makiNotice,
		"msg" : makiMessage,
		"oper" : makiOper,
		"kill" : makiKill,
		"list" : makiList,
		"raw" : makiRaw,
		"whois" : makiWhois,
		"query": tekkaQuery,
		"clear": tekkaClear
	}
