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

import re
import time
from dbus import UInt64

from types import MethodType, FunctionType
from gettext import gettext as _

from . import signals
from . import config
from . import com
from . import gui

from .helper import color
from .helper import markup
from .com import sushi
from .lib.inline_dialog import InlineMessageDialog
from .typecheck import types


def warnNoConnection(tab):
	if tab.is_server():
		name = tab.name
	elif tab.is_channel() or tab.is_query():
		name = tab.server.name

	dialog = InlineMessageDialog(_("Warning:"),
		_("You are not connected to server %(server)s.") % {
			"server": name } )
	dialog.connect("response", lambda w,i: w.destroy() )

	gui.mgmt.show_inline_dialog(dialog)


def warnNotJoined(cTab):
	dialog = InlineMessageDialog(_("Warning:"),
		_("The channel %(channel)s is not joined. Everything you "
		"write will not be send.") % { "channel": cTab.name })
	dialog.connect("response", lambda w,i: w.destroy())

	gui.mgmt.show_inline_dialog(dialog)


def makiConnect(currentServer, currentChannel, args):
	"""
		Connect to the given server.

		Usage: /connect <server>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /connect <servername>")

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
		if gui.tabs.search_tab(args[0]):
			reason = " ".join(args[1:])
			if not reason:
				reason = config.get("chatting", "quit_message", "")
			sushi.quit(args[0], reason)
		else:
			# /quit [<reason>]
			if not currentServer:
				return gui.mgmt.myPrint("Could not determine server.")
			reason = " ".join(args)
			if not reason:
				reason = config.get("chatting", "quit_message", "")
			sushi.quit(currentServer.name, reason)
	else:
		# /quit
		if not currentServer:
			return gui.mgmt.myPrint("Could not determine server.")
		sushi.quit(currentServer.name,
			config.get("chatting", "quit_message", ""))


def makiNick(currentServer, currentChannel, args):
	"""
		Change your current nick to the given nick.

		Usage: /nick <new nick>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /nick <new nick>")

	if not currentServer:
		return gui.mgmt.myPrint("Can't determine my server.")

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
		if gui.tabs.search_tab(currentServer.name, args[0]):
			reason = " ".join(args[1:])
			if not reason:
				reason = config.get("chatting", "part_message", "")
			sushi.part(currentServer.name, args[0], reason)
		else:
			# /part [<reason>]
			if not currentChannel:
				return gui.mgmt.myPrint("Could not determine channel.")
			reason = " ".join(args)
			if not reason:
				reason = config.get("chatting", "part_message", "")
			sushi.part(currentServer.name, currentChannel.name, reason)
	else:
		# /part
		if not currentChannel:
			return gui.mgmt.myPrint("Could not determine channel.")
		sushi.part(currentServer.name, currentChannel.name, config.get("chatting", "part_message", ""))


def makiJoin(currentServer, currentChannel, args):
	"""
		Joins the given channel with the optional key.
		If no channel is given, the command tries to
		join the current activated channel if it's parted.

		Usage: /join [<channel> [<key>]]
	"""
	if not currentServer:
		return gui.mgmt.myPrint("Can't determine server.")

	if not args:
		if currentChannel and not currentChannel.joined:
			return sushi.join(currentServer.name, currentChannel.name, "")
		else:
			return gui.mgmt.myPrint("Usage: /join <channel> [<key>]")

	sushi.join(currentServer.name, args[0], " ".join(args[1:]))


def makiAction(currentServer, currentChannel, args):
	"""
		Sends an action in third person view.

		Usage: /me <text>

		Example: nemo types: /me giggles.
		Results in: nemo giggles.
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /me <text>")

	if not currentChannel:
		return gui.mgmt.myPrint("Can't find active channel.")

	sushi.action(currentServer.name, currentChannel.name, " ".join(args))


def makiKick(currentServer, currentTab, args):
	"""
		Kick the given user with an optional reason from the
		current channel.

		Usage: /kick <user> [<reason>]
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /kick <user> [<reason>]")

	if not currentTab or not currentTab.is_channel():
		return gui.mgmt.myPrint("You're not on a channel")

	sushi.kick(currentServer.name, currentTab.name, args[0], " ".join(args[1:]))


def makiMode(currentServer, currentChannel, args):
	"""
		Sets a mode on the target.

		Usage: /mode <target> (+|-)<mode> [<param>]

		Example: /mode #xesio +o nemo
		OR:	  /mode nemo +x
		OR:	  /mode #xesio +m
	"""
	if not args or len(args) < 1:
		return gui.mgmt.myPrint("Usage: /mode <target> (+|-)<mode> [<param>]")

	if not currentServer:
		return gui.mgmt.myPrint("Could not determine server.")

	if len(args) >= 2:
		# a parameter is given
		sushi.mode(currentServer.name, args[0], "%s %s" % (args[1], " ".join(args[2:])))
	else:
		sushi.mode(currentServer.name, args[0], "")


def makiTopic(serverTab, channelTab, args):
	"""
		Sets the topic in the current channel.
		If no argument is given, print the current topic.

		Usage: /topic [<text>]
	"""
	if not channelTab or not channelTab.is_channel():
		return gui.mgmt.myPrint("No channel active.")

	if not args:
		return gui.mgmt.myPrint(
		"Topic for channel %(channel)s: '%(topic)s'" % {
			"channel": channelTab.name,
			"topic": color.parse_color_codes_to_tags(channelTab.topic)
		}, html=True)

	else:
		topic = " ".join(args)


	sushi.topic(serverTab.name, channelTab.name, topic)


def makiAway(serverTab, channelTab, args):
	"""
		Sets you away with an optional reason.

		Usage: /away [<reason>]
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")

	sushi.away(serverTab.name, " ".join(args))


def makiBack(serverTab, channelTab, args):
	"""
		Sets you back from being away.

		Usage: /back
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")
	sushi.back(serverTab.name)


def makiNickserv(serverTab, channelTab, args):
	"""
		Authenticates you at NickServ with
		the data stored in maki.

		Usage: /nickserv
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")

	sushi.nickserv(serverTab.name)


def makiCTCP(serverTab, channelTab, args):
	"""
		Sends a CTCP message to the given target.

		Usage: /ctcp <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.mgmt.myPrint("Usage: /ctcp <target> <message>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	sushi.ctcp(serverTab.name, args[0], " ".join(args[1:]))


def tekkaNames(serverTab, channelTab, args):
	"""
		Sends a NAMES request and prints the result
		as text to the channel.

		Usage: /names [<channel>]
	"""
	def request(server,channel):
		def names_cb(time, server, channel, nicks, prefixes):
			self = names_cb

			def print_message(message):
				if self.no_channel:
					gui.currentServerPrint(time, server, message,
						"action")
				else:
					gui.channelPrint(time, server, channel, message,
						"action")

			if self.first:
				print_message(_("• Begin of names"))
				self.first = False

			if not nicks: # eol
				signals.disconnect_signal("names", self)
				print_message(_("• End of names"))

			else:
				message = ""
				for i in xrange(len(nicks)):
					message += "[%s<font foreground='%s'>%s</font>]" % (
						prefixes[i],
						color.get_nick_color(nicks[i]),
						nicks[i])

					if (i+1) % 5 == 0:
						print_message(message)
						message = ""
					else:
						message += " "

				print_message(message)


		names_cb.no_channel = not channel
		names_cb.first = True
		signals.connect_signal("names", names_cb)
		sushi.names(server, channel)

	if not args:
		if channelTab:
			request(serverTab.name, channelTab.name)
		else:
			pass # which channel was meant?
	elif len(args) == 1:
		request(serverTab.name, args[0])
	else:
		gui.mgmt.myPrint("Usage: /names [<channel>]")


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
		return gui.mgmt.myPrint("Usage: /notice <target> <message>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	sushi.notice(serverTab.name, args[0], " ".join(args[1:]))


def makiMessage(serverTab, channelTab, args):
	"""
		Sends a message (PRIVMSG) to the target.
		The target can be a channel or a user.

		Usage: /msg <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.mgmt.myPrint("Usage: /msg <target> <message>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	com.sendMessage(serverTab.name, args[0], " ".join(args[1:]))


def makiOper(serverTab, channelTab, args):
	"""
		Authentificate as IRC operator.

		Usage: /oper <user> <pass>
	"""
	if not args or len(args) < 2:
		return gui.mgmt.myPrint("Usage: /oper <user> <pass>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	sushi.oper(serverTab.name, args[0], " ".join(args[1:]))


def makiList(serverTab, channelTab, args):
	"""
		Start a channel listing.
		If channel is given, only the channel
		is listed.

		Usage: /list [<channel>]
	"""
	from .helper import code
	import gobject

	def channelList_cb(time, server, channel, users, topic):
		""" Signal for /list command.
			Prints content of the listing.
		"""

		self = code.init_function_attrs(channelList_cb,
			_text=[],
			_line=0,
			_tab=gui.tabs.search_tab(server))

		def print_listing():
			self._tab.write_raw("<br/>".join(self._text))
			return False

		if not channel and not topic and users == -1:
			# listing ended, reset variables

			def print_end():
				self._tab.write(time, "End of list.")
				return False

			if self._line > 0:
				# print rest
				gobject.idle_add(print_listing)

			gobject.idle_add(print_end)

			code.reset_function_attrs(channelList_cb)

		else:
			self._text.append(("• <b>%s</b><br/>\t%d "+_("User")+"<br/>"+
								"\t"+_("Topic")+": \"%s\"") % (
									markup.escape(channel),
									users,
									markup.escape(topic)))

			self._line += 1

			if self._line == 10:
				gobject.idle_add(print_listing)

				self._text = []
				self._line = 0

	# actual function:
	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	try:
		# channel specific listing?
		channel = args[0]
	except IndexError:
		# start a complete list..
		channel = ""

	serverTab.write(time.time(), "Start of list.")

	signals.connect_signal("list", channelList_cb)
	sushi.list(serverTab.name, channel)

def makiRaw(serverTab, channelTab, args):
	"""
		Sends a command with optional args to maki
		which acts only as forwarder. The command
		goes unchanged to the server.

		Usage: /raw <command> [<further text>]
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /raw <command>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	# upper-case the command
	args[0] = args[0].upper()

	sushi.raw(serverTab.name, " ".join(args))

def makiStopList(serverTab, channelTab, args):
	""" Aborts printing the channel list.

		Usage: /stoplist
	"""
	signals.disconnect_signal("list", signals.channelList_cb)

def makiWhois(currentServer, currentChannel, args):
	"""
		Query a user's identity on the current server.

		Usage: /whois <user mask>
	"""
	def whois_cb(time, server, nick, message):
		""" message = "" => end of whois """

		server_tab = gui.tabs.search_tab(server)

		if message:
			server_tab.write(time,
				_(u"[%(nick)s] %(message)s") % {
					"nick": markup.escape(nick),
					"message": markup.escape(message) })
		else:
			server_tab.write(time,
				_(u"[%(nick)s] End of whois.") % {
					"nick": markup.escape(nick) })


	# begin of command function

	if not args:
		return gui.mgmt.myPrint("No server activated.")

	def handler(time, server, nick, message):
		if message:
			whois_cb(time, server, nick, message)
		else:
			signals.disconnect_signal("whois", handler)

	signals.connect_signal("whois", handler)
	sushi.whois(currentServer.name, args[0])

""" TEKKA USER COMMANDS """

def tekkaQuery(currentServer, currentTab, args):
	"""
		Starts a query dialog with the given user.

		Usage: /query <nick>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /query <nick>")

	if not currentServer:
		return gui.mgmt.myPrint("Can't determine server.")

	nick = args[0]

	tab = gui.tabs.search_tab(currentServer.name, nick)
	if not tab:
		# no query started

		tab = gui.tabs.create_query(currentServer, nick)
		tab.connected = True

		gui.tabs.add_tab(currentServer, tab)
		gui.shortcuts.assign_numeric_tab_shortcuts(gui.tabs.get_all_tabs())

		output = tab.window.textview.get_buffer()

		# fetch and write history to query (if any)
		tab.print_last_log()
	else:
		# jump to query
		tab.switch_to()

def tekkaClear(currentServer, currentTab, args):
	"""
		Clears the output of the current channel.

		Usage: /clear
	"""
	gui.mgmt.clear_all_outputs()

def tekkaHelp(currentServer, currentTab, args):
	"""
		Prints the doc-string of the given command.

		Usage: /help <command>
	"""
	global _commands
	if not args:
		return gui.mgmt.myPrint("Usage: /help <command>")
	if _commands.has_key(args[0]):
		gui.mgmt.myPrint(_commands[args[0]].__doc__.replace("\t",""))
	else:
		gui.mgmt.myPrint("No help for %s available." % (args[0]))


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
	"names" : tekkaNames,
	"notice" : makiNotice,
	"msg" : makiMessage,
	"oper" : makiOper,
	"list" : makiList,
	"raw" : makiRaw,
	"stoplist" : makiStopList,
	"whois" : makiWhois,
	"query": tekkaQuery,
	"clear": tekkaClear,
	"help": tekkaHelp
}

_builtins = _commands.keys()

@types(text=basestring)
def parseInput(text):
	"""
	parse color codes (%Cn[,m]),
	split text for blank, strip the command
	and search for it in _commands-dict.
	Call the underlying function if found.
	"""
	if not text:
		return

	# parse %C tags
	text = color.parse_color_markups_to_codes(text)

	serverTab,channelTab = gui.tabs.get_current_tabs()

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
			return gui.mgmt.myPrint("No command given.")

		# search for the command
		global _commands

		if not _commands.has_key(cmd):
			# command not found, look if we
			# can send it as RAW.

			if not serverTab:
				return gui.mgmt.myPrint("No server active.")

			# build raw command
			raw = cmd.upper()

			if len(argv) > 1:
				raw +=  " " + " ".join(argv[1:])

			gui.mgmt.myPrint(_(
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

