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

from gettext import gettext as _

from tekka import com
from tekka import config
from tekka import commands
from tekka import signals
from tekka import config
from tekka import gui

"""
TYPE_STRING: Takes one argument (default string)
TYPE_PASSWORD: Hidden string. Takes one argument (default string)
TYPE_NUMBER: Takes one argument (default number)
TYPE_BOOL: Takes one argument (default bool value)
TYPE_CHOICE: Takes n key/value tuple and a default index.
"""
(TYPE_STRING,
 TYPE_PASSWORD,
 TYPE_NUMBER,
 TYPE_BOOL,
 TYPE_CHOICE
) = range(5)


class Plugin (object):


	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

		self.__signals = {}
		self.__commands = {}

		com.sushi.g_connect("maki-connected", self.maki_connected)
		com.sushi.g_connect("maki-disconnected", self.maki_disconnected)


	def unload(self):
		""" unregister all signals and commands used by
			this plugin
		"""

		for (signal, hlist) in self.__signals:
			for handler in hlist:
				signals.disconnect_signal(signal, handler)

		for (command, handler) in self.__commands:
			commands.remove_command(command, handler)


	def maki_connected(self, interface):
		""" hook, called if connection to maki is etablished """
		pass


	def maki_disconnected(self, interface):
		""" hook, called if connection to maki is cut """
		pass


	def display_error(self, message):

		gui.mgmt.show_inline_message(
			_("Plugin “%(plugin)s” caused an error.") % {
				"plugin": self._plugin_name
			}, "%(message)s" % {
				"message": message
			}, dtype="error")


	def get_bus(self):

		return com.sushi


	def get_nick(self, server):
		nick = com.get_own_nick(server)

		if not nick:
			return None

		return nick


	def add_command(self, command, func):

		def func_proxy (server, target, args):
			return func(server.name, target.name, args)

		if commands.add_command(command, func_proxy):
			self.__commands[command] = func_proxy
			return True

		return False


	def remove_command(self, command):

		if commands.remove_command(command):
			del self.__commands[commands]
			return True

		return False


	def connect_signal(self, signal, func):

		if signals.connect_signal(signal, func):

			if self.__signals.has_key(signal):
				self.__signals[signal].append(func)
			else:
				self.__signals[signal] = [func]
			return True

		return False


	def disconnect_signal(self, signal, func):

		if signals.disconnect_signal(signal, func):

			i = self.__signals[signal].index(func)
			del self.__signals[signal][i]
			return True

		return False


	def set_config(self, name, value):

		section = "plugin_%s" % (self._plugin_name)

		config.create_section(section)

		return config.set(section, name, value)


	def get_config(self, name, default = None):

		section = "plugin_%s" % (self._plugin_name)

		return config.get(section, name, default)


	def parse_from(self, host):
		return com.parse_from(host)
