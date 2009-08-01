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

import time
from dbus import UInt64

from types import MethodType, FunctionType
from typecheck import types

from gettext import gettext as _

import config
import com
import gui_control as gui
from lib.inline_dialog import InlineMessageDialog

sushi = com.sushi

def warnNoConnection(tab):
	if tab.is_server():
		name = tab.name
	elif tab.is_channel() or tab.is_query():
		name = tab.server

	dialog = InlineMessageDialog(_("Warning:"), _("You are not connected to "
		"server %(server)s.")  % { "server": name } )
	dialog.connect("response", lambda w,i: w.destroy() )

	gui.showInlineDialog(dialog)

def warnNotJoined(cTab):
	dialog = InlineMessageDialog(_("Warning:"), _("The channel "
		"%(channel)s is not joined. Everything you write will "
		"not be send.") % { "channel": cTab.name })
	dialog.connect("response", lambda w,i: w.destroy())

	gui.showInlineDialog(dialog)

def makiConnect(currentServer, currentChannel, args):
	"""
		Connect to the given server.

		Usage: /connect <server>
	"""
	if not args:
		return gui.myPrint("Usage: /connect <servername>")

	sushi.connect(args[0])

def makiQuit(currentServer, currentChannel, args):
	"""
		Quit the given server with an optional reason.
		If no server is given, the current server is quit.

		Usage: /quit <server> [<reason>]
			   /quit [<reason>]
	"""
	if args:
		# /quit <server> [<reason>]
		if gui.tabs.searchTab(args[0]):
			reason = " ".join(args[1:])
			if not reason:
				reason = config.get("chatting", "quit_message", "")
			sushi.quit(args[0], reason)
		else:
			# /quit [<reason>]
			if not currentServer:
				return gui.myPrint("Could not determine server.")
			reason = " ".join(args)
			if not reason:
				reason = config.get("chatting", "quit_message", "")
			sushi.quit(currentServer.name, reason)
	else:
		# /quit
		if not currentServer:
			return gui.myPrint("Could not determine server.")
		sushi.quit(currentServer.name, config.get("chatting", "quit_message", ""))

def makiNick(currentServer, currentChannel, args):
	"""
		Change your current nick to the given nick.

		Usage: /nick <new nick>
	"""
	if not args:
		return gui.myPrint("Usage: /nick <new nick>")

	if not currentServer:
		return gui.myPrint("Can't determine my server.")

	sushi.nick(currentServer.name, args[0])

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
			reason = " ".join(args[1:])
			if not reason:
				reason = config.get("chatting", "part_message", "")
			sushi.part(currentServer.name, args[0], reason)
		else:
			# /part [<reason>]
			if not currentChannel:
				return gui.myPrint("Could not determine channel.")
			reason = " ".join(args)
			if not reason:
				reason = config.get("chatting", "part_message", "")
			sushi.part(currentServer.name, currentChannel.name, reason)
	else:
		# /part
		if not currentChannel:
			return gui.myPrint("Could not determine channel.")
		sushi.part(currentServer.name, currentChannel.name, config.get("chatting", "part_message", ""))

def makiJoin(currentServer, currentChannel, args):
	"""
		Joins the given channel with the optional key.
		If no channel is given, the command tries to
		join the current activated channel if it's parted.

		Usage: /join [<channel> [<key>]]
	"""
	if not currentServer:
		return gui.myPrint("Can't determine server.")

	if not args:
		if currentChannel and not currentChannel.joined:
			return sushi.join(currentServer.name, currentChannel.name, "")
		else:
			return gui.myPrint("Usage: /join <channel> [<key>]")

	sushi.join(currentServer.name, args[0], " ".join(args[1:]))

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

	sushi.action(currentServer.name, currentChannel.name, " ".join(args))

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

	sushi.kick(currentServer.name, currentTab.name, args[0], " ".join(args[1:]))

def makiMode(currentServer, currentChannel, args):
	"""
		Sets a mode on the target.

		Usage: /mode <target> (+|-)<mode> [<param>]

		Example: /mode #xesio +o nemo
		OR:	  /mode nemo +x
		OR:	  /mode #xesio +m
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /mode <target> (+|-)<mode> [<param>]")

	if not currentServer:
		return gui.myPrint("Could not determine server.")

	if len(args) > 2:
		# a parameter is given
		sushi.mode(currentServer.name, args[0], "%s %s" % (args[1], " ".join(args[2:])))
	else:
		sushi.mode(currentServer.name, args[0], args[1])

def makiTopic(serverTab, channelTab, args):
	"""
		Sets the topic in the current channel.
		If no argument is given, print the current topic.

		Usage: /topic [<text>]
	"""
	if not channelTab or not channelTab.is_channel():
		return gui.myPrint("No channel active.")

	if not args:
		return gui.myPrint(
		"Topic for channel %(channel)s: '%(topic)s'" % {
			"channel":channelTab.name,
			"topic":channelTab.topic
		})

	else:
		topic = " ".join(args)


	sushi.topic(serverTab.name, channelTab.name, topic)

def makiAway(serverTab, channelTab, args):
	"""
		Sets you away with an optional reason.

		Usage: /away [<reason>]
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")

	sushi.away(serverTab.name, " ".join(args))

def makiBack(serverTab, channelTab, args):
	"""
		Sets you back from being away.

		Usage: /back
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")
	sushi.back(serverTab.name)

def makiNickserv(serverTab, channelTab, args):
	"""
		Authenticates you at NickServ with
		the data stored in maki.

		Usage: /nickserv
	"""
	if not serverTab:
		return gui.myPrint("Can't determine server.")

	sushi.nickserv(serverTab.name)

def makiCTCP(serverTab, channelTab, args):
	"""
		Sends a CTCP message to the given target.

		Usage: /ctcp <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /ctcp <target> <message>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	sushi.ctcp(serverTab.name, args[0], " ".join(args[1:]))

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

	sushi.notice(serverTab.name, args[0], " ".join(args[1:]))

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

	com.sendMessage(serverTab.name, args[0], " ".join(args[1:]))

def makiOper(serverTab, channelTab, args):
	"""
		Authentificate as IRC operator.

		Usage: /oper <user> <pass>
	"""
	if not args or len(args) < 2:
		return gui.myPrint("Usage: /oper <user> <pass>")

	if not serverTab:
		return gui.myPrint("Could not determine server.")

	sushi.oper(serverTab.name, args[0], " ".join(args[1:]))

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
	sushi.list(serverTab.name, channel)

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

	sushi.raw(serverTab.name, " ".join(args))

def makiWhois(currentServer, currentChannel, args):
	"""
		Query a user's identity on the current server.

		Usage: /whois <user mask>
	"""
	if not args:
		return gui.myPrint("No server activated.")

	sushi.whois(currentServer.name, args[0])

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
		gui.updateServerTreeShortcuts()

		output = tab.textview.get_buffer()

		# fetch and write history to query (if any)
		for line in sushi.log(currentServer.name, nick,
			UInt64(config.get("chatting","last_log_lines","10"))):

			output.insertHTML(output.get_end_iter(),
				"<font foreground='#DDDDDD'>%s</font>" % gui.escape(line))

def tekkaClear(currentServer, currentTab, args):
	"""
		Clears the output of the current channel.

		Usage: /clear
	"""
	if currentTab:
		currentTab.textview.get_buffer().set_text("")
	elif currentServer:
		currentServer.textview.get_buffer().set_text("")

def tekkaHelp(currentServer, currentTab, args):
	"""
		Prints the doc-string of the given command.

		Usage: /help <command>
	"""
	global _commands
	if not args:
		return gui.myPrint("Usage: /help <command>")
	if _commands.has_key(args[0]):
		gui.myPrint(_commands[args[0]].__doc__.replace("\t",""))
	else:
		gui.myPrint("No help for %s available." % (args[0]))


_commands = {
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
	"list" : makiList,
	"raw" : makiRaw,
	"whois" : makiWhois,
	"query": tekkaQuery,
	"clear": tekkaClear,
	"help": tekkaHelp
}

_builtins = _commands.keys()

@types(text=basestring)
def parseInput(text):
	"""
	split text for blank, strip the command
	and search for it in _commands-dict.
	Call the underlying function if found.
	"""
	if not text:
		return

	serverTab,channelTab = gui.tabs.getCurrentTabs()

	if ((channelTab and not channelTab.connected)
		or (serverTab and not serverTab.connected)):
		# there is no connection in this tab so
		# if you're typing something, it would have
		# no effect. So warn the user.
		warnNoConnection(serverTab)

	if text[0] != "/" or text[:2] == "//":
		# this is no command

		if not channelTab:
			# no command AND no channel is nonsense.
			# normal text is useless in context
			# with server tabs
			return

		# strip first slash if it's a fake command
		if text[0] == "/":
			text = text[1:]

		if channelTab.is_channel() and not channelTab.joined:
			warnNotJoined(channelTab)

		com.sendMessage(serverTab.name, channelTab.name, text)

	else:
		# we got a command here

		argv = text[1:].split(" ")
		cmd = argv[0]

		if not cmd:
			# / typed
			return gui.myPrint("No command given.")

		# search for the command
		global _commands

		if not _commands.has_key(cmd):
			# command not found, look if we
			# can send it as RAW.

			if not serverTab:
				return gui.myPrint("No server active.")

			# build raw command
			raw = cmd.upper()

			if len(argv) > 1:
				raw +=  " " + " ".join(argv[1:])

			gui.myPrint(_(
				u"• Unknown command “%(command)s”, "\
				u"sending raw command “%(raw)s”.") % {
					"command": cmd,
					"raw": raw })
			sushi.raw(serverTab.name, raw)

		else:
			_commands[cmd](serverTab, channelTab, argv[1:])


@types(command=basestring,function=(MethodType,FunctionType))
def addCommand(command, function):
	"""
		Add a command.
		Returns True on success, otherwise False.
	"""
	global _commands

	if _commands.has_key(command):
		return False

	_commands[command] = function

	return True

@types(command=basestring)
def removeCommand(command):
	"""
		Removes a command.
		Returns True on success, otherwise False.
	"""
	global _commands, _builtins

	if _commands.has_key(command) and command not in _builtins:
		del _commands[command]
		return True

	return False

