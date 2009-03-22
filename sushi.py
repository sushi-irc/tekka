import com
import commands
import signals
import config

class Plugin (object):

	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

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

	def get_config(self, name):
		section = "plugin_%s" % (self._plugin_name)

		return config.get(section, name)
