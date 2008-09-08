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
from dbus import UInt64

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

	if text[0] != "/":
		if not channelTab:
			return
		com.sendMessage(serverTab.name, channelTab.name, text)
	elif text[:2] == "//":
		if not channelTab:
			return
		com.sendMessage(serverTab.name, channelTab.name, text[1:])
	else:
		list = text[1:].split(" ")
		cmd = list[0]

		if not cmd:
			return gui.myPrint("No command given.")
		elif not commands.has_key(cmd):
			if not serverTab:
				return gui.myPrint("No server active.")
			gui.myPrint("Unknown command '%s'; Forwarding raw." % (cmd))
			com.raw(serverTab.name, cmd.upper() + " ".join(list[1:]))

		else:
			commands[cmd](serverTab, channelTab, list[1:])

def makiConnect(currentServer, currentChannel, args):
	"""
		Connect to the given server.

		Usage: /connect <server>
	"""
	if not args:
		return gui.myPrint("Usage: /connect <servername>")

	com.connectServer(args[0])

def makiQuit(currentServer, currentChannel, args):
	"""
		Quit the given server with an optional reason.
		If no server is given, the current server is quit.

		Usage: /quit <server> [<reason>]
		       /quit [<reason>]
	"""
	if args:
		# /quit <server> [<reason>]
		if gui.tabs.searchTab(None, args[0]):
			com.quitServer(args[0], " ".join(args[1:]))
		else:
			# /quit [<reason>]
			if not currentServer:
				return gui.myPrint("Could not determine server.")
			com.quitServer(currentServer.name, " ".join(args))
	else:
		# /quit
		if not currentServer:
			return gui.myPrint("Could not determine server.")
		com.quitServer(currentServer.name,"")

def makiNick(currentServer, currentChannel, args):
	"""
		Change your current nick to the given nick.

		Usage: /nick <new nick>
	"""
	if not args:
		return gui.myPrint("Usage: /nick <new nick>")

	if not currentServer:
		return gui.myPrint("Can't determine my server.")

	com.nick(currentServer.name, args[0])

def makiPart(currentServer, currentChannel, args):
	"""
		Part the given channel with an optional reason.
		If no channel is given, the current channel is parted.

		Usage: /part <channel> [<reason>]
		       /part [<reason>]
	"""
	if args and currentServer:
		# /part <channel> [<reason>]
		if gui.tabs.searchTab(currentServer.name, args[0]):
			com.part(args[0], " ".join(args[1:]))
		else:
			# /part [<reason>]
			if not currentChannel:
				return gui.myPrint("Could not determine channel.")
			com.part(currentServer.name, currentChannel.name, " ".join(args))
	else:
		# /part
		if not currentChannel:
			return gui.myPrint("Could not determine channel.")
		com.part(currentServer.name, currentChannel.name,"")

def makiJoin(currentServer, currentChannel, args):
	"""
		Joins the given channel with the optional key.

		Usage: /join <channel> [<key>]
	"""
	if not currentServer:
		return gui.myPrint("Can't determine server.")

	if not args:
		return gui.myPrint("Usage: /join <channel> [<key>]")

	com.join(currentServer.name, args[0], " ".join(args[1:]))

def makiAction(currentServer, currentChannel, args):
	"""
		Sends an action in third person view.

		Usage: /me <text>

		Example: nemo types: /me giggles.
		Results in: nemo giggles.
	"""
	if not args:
		return gui.myPrint("Usage: /me <text>")

	if not currentChannel:
		return gui.myPrint("Can't find active channel.")

	com.action(currentServer.name, currentChannel.name, " ".join(args))

def makiKick(currentServer, currentTab, args):
	"""
		Kick the given user with an optional reason from the
		current channel.

		Usage: /kick <user> [<reason>]
	"""
	if not args:
		return gui.myPrint("Usage: /kick <user> [<reason>]")

	if not currentTab or not currentTab.is_channel():
		return gui.myPrint("You're not on a channel")

	com.kick(currentServer.name, currentTab.name, args[0], " ".join(args[1:]))

def makiMode(currentServer, currentChannel, args):
	"""
		Sets a mode on the target.

		Usage: /mode <target> (+|-)<mode> [<param>]

		Example: /mode #xesio +o nemo
		OR:      /mode nemo +x
		OR:      /mode #xesio +m
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /mode <target> (+|-)<mode> [<param>]")

	if not currentServer:
		return gui.myPrint("Could not determine server.")

	if len(args) > 2:
		# a parameter is given
		param = " ".join(args[2:])

	com.mode(currentServer.name, args[0], "%s %s" % (args[1],param))

def makiTopic(serverTab, channelTab, args):
	"""
		Sets the topic in the current channel.

		Usage: /topic <text>
	"""
	if not args:
		return gui.myPrint("Usage: /topic <text>")
	else:
		topic = " ".join(args)

	if not channelTab or not channelTab.is_channel():
		return gui.myPrint("No channel active.")

	com.setTopic(serverTab.name, channelTab.name, topic)

def makiAway(serverTab, channelTab, args):
	"""
		Sets you away with an optional reason.

		Usage: /away [<reason>]
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")

	com.setAway(serverTab.name, " ".join(args))

def makiBack(serverTab, channelTab, args):
	"""
		Sets you back from being away.

		Usage: /back
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")
	com.setBack(serverTab.name)

def makiNickserv(serverTab, channelTab, args):
	"""
		Authenticates you at NickServ with
		the data stored in maki.

		Usage: /nickserv
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")

	com.nickserv(server)

def makiCTCP(serverTab, channelTab, args):
	"""
		Sends a CTCP message to the given target.

		Usage: /ctcp <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /ctcp <target> <message>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	com.ctcp(serverTab.name, args[0], args[1])

def makiNotice(serverTab, channelTab, args):
	"""
		Sends a notice to the given target.
		The difference between /ctcp and /notice
		is, that /ctcp sends directly to the user
		while /notice sends the message over the
		server.

		Usage: /notice <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /notice <target> <message>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	com.notice(serverTab.name, args[0], " ".join(args[1:]))

def makiMessage(serverTab, channelTab, args):
	"""
		Sends a message (PRIVMSG) to the target.
		The target can be a channel or a user.

		Usage: /msg <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /msg <target> <message>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	com.sendMessage(serverTab.name, args[0], " ".join(args[1]))

def makiOper(serverTab, channelTab, args):
	"""
		Authentificate as IRC operator.

		Usage: /oper <user> <pass>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /oper <user> <pass>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	com.oper(serverTab.name, args[0], " ".join(args[1:]))

def makiKill(serverTab, channelTab, args):
	"""
		Kill a user on the network with an optional reason.

		Usage: /kill <user> [<reason>]
	"""
	if not args or len(args) < 1:
		return gui.myPrint("Usage: /kill <user> [<reason>]")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	com.kill(serverTab.name, args[0], " ".join(args[1:]))

def makiList(serverTab, channelTab, args):
	"""
		Start a channel listing.
		If channel is given, only the channel
		is listed.

		Usage: /list [<channel>]
	"""
	if not serverTab:
		return gui.myPrint("Could not determine server.")

	try:
		# channel specific listing?
		channel = args[0]
	except IndexError:
		# start a complete list..
		channel = ""

	gui.serverPrint(time.time(), serverTab.name, "Start of list.")
	com.list(serverTab.name, channel)

def makiRaw(serverTab, channelTab, args):
	"""
		Sends a command with optional args to maki
		which acts only as forwarder. The command
		goes unchanged to the server.

		Usage: /raw <command> [<further text>]
	"""
	if not args:
		return gui.myPrint("Usage: /raw <command>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	# upper-case the command
	args[0] = args[0].upper()

	com.raw(server, " ".join(args))

def makiWhois(currentServer, currentChannel, args):
	"""
		Query a user's identity on the current server.

		Usage: /whois <user mask>
	"""
	if not args:
		return gui.myPrint("No server activated.")

	com.sushi.whois(currentServer.name, args[0])

""" TEKKA USER COMMANDS """

def tekkaQuery(currentServer, currentTab, args):
	"""
		Starts a query dialog with the given user.

		Usage: /query <nick>
	"""
	if not args:
		return gui.myPrint("Usage: /query <nick>")

	if not currentServer:
		return gui.myPrint("Can't determine server.")

	nick = args[0]

	if not gui.tabs.searchTab(currentServer.name, nick):
		# no query started

		tab = gui.tabs.createQuery(currentServer.name, nick)
		tab.connected = True
		gui.tabs.addTab(currentServer.name, tab)

		output = tab.buffer

		# fetch and write history to query (if any)
		for line in com.fetchLog(currentServer.name, nick,
			UInt64(config.get("chatting","last_log_lines","10"))):

			output.insertHTML(output.get_end_iter(),
				"<font foreground='#DDDDDD'>%s</font>" % gui.escape(line))

def tekkaClear(currentServer, currentTab, args):
	"""
		Clears the output of the current channel.

		Usage: /clear
	"""
	if currentTab: currentTab.buffer.set_text("")
	elif currentServer: currentServer.buffer.set_text("")

def tekkaHelp(currentServer, currentTab, args):
	"""
		Prints the doc-string of the given command.

		Usage: /help <command>
	"""
	if not args:
		return gui.myPrint("Usage: /help <command>")
	if commands.has_key(args[0]):
		gui.myPrint(commands[args[0]].__doc__.replace("\t",""))
	else:
		gui.myPrint("No help for %s available." % (args[0]))

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
		"clear": tekkaClear,
		"help": tekkaHelp
	}
