import com
import commands
import signals
import config

class Plugin (object):

	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

	def get_bus(self):
		return com.sushi

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

	def set_config_value(self, name, value):
		config.create_section("plugin_%s" % (self._plugin_name))
		return config.set("plugin_%s" % (self._plugin_name), name, value)

	def get_config_value(self, name):
		return config.get("plugin_%s" % (self._plugin_name), name)
