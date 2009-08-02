# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
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

import com
import commands
import signals
import config

import lib.gui_control as gui_control
from lib.inline_dialog import InlineMessageDialog

class Plugin (object):

	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

	def display_error(self, message):
		d = InlineMessageDialog("Plugin “%(plugin)s” caused an error." % {
				"plugin": self._plugin_name
			}, "%(message)s" % {
				"message": message
			})
		gui_control.showInlineDialog(d)
		d.connect("response", lambda d,id: d.destroy())

	def get_bus(self):
		return com.sushi

	def get_nick(self, server):
		nick = com.getOwnNick(server)

		if not nick:
			return None

		return nick

	def add_command(self, command, func):
		def func_proxy (server, target, args):
			return func(server.name, target.name, args)

#		self.emit("command_add", command, func)
		return commands.addCommand(command, func_proxy)

	def remove_command(self, command):
#		self.emit("command_remove", command, func)
		return commands.removeCommand(command)

	def connect_signal(self, signal, func):
#		self.emit("signal_connect", signal, func)
		return signals.connect_signal(signal, func)

	def disconnect_signal(self, signal, func):
#		self.emit("signal_disconnect", signal, func)
		return signals.disconnect_signal(signal, func)

	def set_config(self, name, value):
		section = "plugin_%s" % (self._plugin_name)

		config.create_section(section)

		return config.set(section, name, value)

	def get_config(self, name, default = None):
		section = "plugin_%s" % (self._plugin_name)

		return config.get(section, name, default)
