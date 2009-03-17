"""
plugin interface

load(filename)
-> imp(filename)
-> plugins[filename] = <filename>.filename(pluginInterface)

unload(filename)
-> plugins[filename].unload()
-> del plugins[filename]
"""

import gobject
import os

import com

_plugins = {}

class PluginInterface(gobject.GObject):

	def __init__(self):
		pass

	def get_dbus_interface(self):
		return com.sushi

	def add_command(self, command, func):
		self.emit("command_add", command, func)
		return commands.addCommand(command, func)

	def remove_command(self, command, func):
		self.emit("command_remove", command, func)
		return commands.removeCommand(command, func)

	def connect_signal(self, signal, func):
		self.emit("signal_connect", signal, func)
		return signals.connect_signal(signal, func)

	def disconnect_signal(self, signal, func):
		self.emit("signal_disconnect", signal, func)
		return signals.disconnect_signal(signal, func)

def strip_suffix(filename):
	""" foo.py -> foo """
	return os.path.split(filename)[-1].split(".")[0]

def _register_plugin(filename, module, instance):
	return True

def _unregister_plugin(filename):
	return True

def load(filename):
	name = strip_suffix(filename)

	modInfo = None
	try:
		modInfo = imp.find_module(
			name, config.get_list("plugins","path")
	except ImportError, e:
		print "Error while finding module for '%s'" % (filename)
		return False

	if not modTuple:
		print "No plugin found for filename '%s'" % (filename)
		return False

	plugin = None
	try:
		plugin = imp.load_module(name, *modTuple)
	except ImportError,e:
		print "Failure while loading plugin '%s': " % (name), e

	try:
		modTuple[0].close()
	except (IndexError,AttributeError):
		pass

	if not plugin:
		return False

	try:
		instance = eval ("plugin.%s(pluginInterface())" % (name))
	except BaseException,e:
		print "Error while instancing plugin: %s" % (e)
		return False

	return _register_plugin(filename, plugin, instance)

def unload(filename):
	return False
