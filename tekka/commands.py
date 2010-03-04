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
from types import MethodType, FunctionType

from . import gui
from . import com

from .helper import color
from .com import sushi
from .typecheck import types

_commands = {}

@types(text=basestring)
def parseInput(text):
	"""
	parse color codes (%Cn[,m]),
	split text for blank, strip the command
	and search for it in _commands-dict.
	Call the underlying function if found.
	Paramters for the function are:
	- the current server or None
	- the current channel or None
	- A list of words typed after the command
	  ("parameters") split by space
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

		argv = text[1:].rstrip().split(" ")
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
def add_command(command, function):
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
def remove_command(command):
	"""
		Removes a command.
		Returns True on success, otherwise False.
	"""
	global _commands

	if _commands.has_key(command):
		del _commands[command]
		return True

	return False

