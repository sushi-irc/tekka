# coding: UTF-8
"""
Copyright (c) 2010 Marian Tietz
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

from gettext import gettext as _

from tekka.lib.inline_dialog import InlineMessageDialog
from tekka.helper import code
from tekka.helper import color
from tekka.helper import markup

from tekka import com
from tekka import gui
from tekka import config
from tekka import signals
from tekka import commands

from tekka.com import sushi

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






def cmd_connect(currentServer, currentChannel, args):
	"""
		Connect to the given server.

		Usage: /connect <server>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /connect <servername>")

	sushi.connect(args[0])


def cmd_quit(currentServer, currentChannel, args):
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


def cmd_nick(currentServer, currentChannel, args):
	"""
		Change your current nick to the given nick.

		Usage: /nick <new nick>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /nick <new nick>")

	if not currentServer:
		return gui.mgmt.myPrint("Can't determine my server.")

	sushi.nick(currentServer.name, args[0])


def cmd_part(currentServer, currentChannel, args):
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


def cmd_join(currentServer, currentChannel, args):
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


def cmd_action(currentServer, currentChannel, args):
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


def cmd_kick(currentServer, currentTab, args):
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


def cmd_mode(currentServer, currentChannel, args):
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


def cmd_topic(serverTab, channelTab, args):
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


def cmd_away(serverTab, channelTab, args):
	"""
		Sets you away with an optional reason.

		Usage: /away [<reason>]
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")

	sushi.away(serverTab.name, " ".join(args))
	serverTab.current_write(time.time(), _("You are now away."))


def cmd_back(serverTab, channelTab, args):
	"""
		Sets you back from being away.

		Usage: /back
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")

	sushi.back(serverTab.name)
	serverTab.current_write(time.time(), _("You are now back."))


def cmd_nickserv(serverTab, channelTab, args):
	"""
		Authenticates you at NickServ with
		the data stored in maki.

		Usage: /nickserv
	"""
	if not serverTab:
		return gui.mgmt.myPrint("Can't determine server.")

	sushi.nickserv(serverTab.name)


def cmd_ctcp(serverTab, channelTab, args):
	"""
		Sends a CTCP message to the given target.

		Usage: /ctcp <target> <message>
	"""
	if not args or len(args) < 2:
		return gui.mgmt.myPrint("Usage: /ctcp <target> <message>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	sushi.ctcp(serverTab.name, args[0], " ".join(args[1:]))


def cmd_names(serverTab, channelTab, args):
	"""
		Sends a NAMES request and prints the result
		as text to the channel.

		Usage: /names [<channel>]
	"""
	def request(server,channel):
		""" print the name listing in the queried tab (if it's active)
			or in the current tab
		"""
		def names_cb(time, server, channel, nicks, prefixes):

			self = names_cb

			def print_message(message):
				if self.tab.is_active():
					# print in the channel we query
					self.tab.write(time, message, "action")
				elif self.tab.is_server():
					self.tab.current_write(time, message, "action")
				else:
					# print in the current channel
					self.tab.server.current_write(time, message, "action")

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

					if (i+1) % self.max_col == 0:
						print_message(message)
						message = ""
					else:
						message += " "

				print_message(message)


		names_cb.first = True
		names_cb.max_col = int(config.get("tekka","names_columns"))
		s,c = gui.tabs.search_tabs(server, channel)
		names_cb.tab = c or s

		signals.connect_signal("names", names_cb)
		sushi.names(server, channel)

	if channelTab and not channelTab.is_channel():
		gui.mgmt.myPrint("/names can only be used on channel tabs.")
		return

	if not args:
		if channelTab:
			request(serverTab.name, channelTab.name)
		else:
			pass # which channel was meant?
	elif len(args) == 1:
		request(serverTab.name, args[0])
	else:
		gui.mgmt.myPrint("Usage: /names [<channel>]")


def cmd_notice(serverTab, channelTab, args):
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


def cmd_message(serverTab, channelTab, args):
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


def cmd_oper(serverTab, channelTab, args):
	"""
		Authentificate as IRC operator.

		Usage: /oper <user> <pass>
	"""
	if not args or len(args) < 2:
		return gui.mgmt.myPrint("Usage: /oper <user> <pass>")

	if not serverTab:
		return gui.mgmt.myPrint("Could not determine server.")

	sushi.oper(serverTab.name, args[0], " ".join(args[1:]))


def cmd_list(serverTab, channelTab, args):
	"""
		Start a channel listing.
		If channel is given, only the channel
		is listed.

		Usage: /list [<channel>]
	"""
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

			self._text = []
			self._line = 0
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

			signals.disconnect_signal("list", channelList_cb)

		else:
			self._text.append(("• <b>%s</b><br/>\t%d "+_("User")+"<br/>"+
								"\t"+_("Topic")+": \"%s\"") % (
									markup.escape(channel),
									users,
									markup.escape(topic)))
			self._line += 1

			if self._line == 10:

				gobject.idle_add(print_listing)


	# cmd_list:

	# make the callback accessible for cmd_stop_list
	cmd_list.list_cb = channelList_cb

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


def cmd_raw(serverTab, channelTab, args):
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


def cmd_stop_list(serverTab, channelTab, args):
	""" Aborts printing the channel list.

		Usage: /stoplist
	"""
	try:
		signals.disconnect_signal("list", cmd_list.list_cb)
	except AttributeError:
		# already stopped
		return


def cmd_whois(currentServer, currentChannel, args):
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


def cmd_query(currentServer, currentTab, args):
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


def cmd_clear(currentServer, currentTab, args):
	"""
		Clears the output of the current channel.

		Usage: /clear
	"""
	gui.mgmt.clear_all_outputs()


def cmd_help(currentServer, currentTab, args):
	"""
		Prints the doc-string of the given command.

		Usage: /help <command>
	"""
	if not args:
		return gui.mgmt.myPrint("Usage: /help <command>")
	if commands._commands.has_key(args[0]):
		gui.mgmt.myPrint(commands._commands[args[0]].__doc__.replace("\t",""))
	else:
		gui.mgmt.myPrint("No help for %s available." % (args[0]))


def cmd_invoke_test(currentServer, currentTab, args):
	"""
		Loads a test file and executes it.

		Usage: /invoke_test <path>
	"""
	if len(args) != 1:
		return gui.myPrint("Usage: /invoke_test <path>")

	import os
	import imp

	path, file = os.path.split(args[0])

	name = file.split(".")[0]

	try:
		mod_info = imp.find_module(name, [path])
		test_module = imp.load_module(name, *mod_info)

	except ImportError as e:
		gui.mgmt.myPrint("invoke_test failed: %s" % (e))
		return

	try:
		test_module.start_test(gui)
	except Exception as e:
		gui.mgmt.myPrint("invoke_test run failed: %s" % (e))
		return


def setup():
	_commands = {
		"connect" : cmd_connect,
		"nick" : cmd_nick,
		"part" : cmd_part,
		"join" : cmd_join,
			"j" : cmd_join,
		"me"   : cmd_action,
		"kick" : cmd_kick,
		"mode" : cmd_mode,
		"topic": cmd_topic,
		"quit" : cmd_quit,
		"away" : cmd_away,
		"back" : cmd_back,
	"nickserv" : cmd_nickserv,
		"ctcp" : cmd_ctcp,
	"invoke_test": cmd_invoke_test,
		"names" :  cmd_names,
		"notice" : cmd_notice,
		"msg" : cmd_message,
		"oper" : cmd_oper,
		"list" : cmd_list,
		"raw" : cmd_raw,
		"stoplist" : cmd_stop_list,
		"whois" : cmd_whois,
		"query":  cmd_query,
		"clear":  cmd_clear,
		"help":  cmd_help
	}

	for (cmd,hdl) in _commands.items():
		commands.add_command(cmd, hdl)
