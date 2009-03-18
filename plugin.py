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
import imp
import sys

import com
import commands
import signals
import config
from gui_control import errorMessage

_module_prefix = "tekkaplugin_"
_plugins = {}

class PluginInterface(gobject.GObject):

	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

	def get_dbus(self):
		return com.sushi

	def add_command(self, command, func):
#		self.emit("command_add", command, func)
		return commands.addCommand(command, func)

	def remove_command(self, command, func):
#		self.emit("command_remove", command, func)
		return commands.removeCommand(command, func)

	def connect_signal(self, signal, func):
#		self.emit("signal_connect", signal, func)
		return signals.connect_signal(signal, func)

	def disconnect_signal(self, signal, func):
#		self.emit("signal_disconnect", signal, func)
		return signals.disconnect_signal(signal, func)

	def set_config_value(self, name, value):
		config.create_section("plugin_%s" % (self.plugin_name))
		return config.set("plugin_%s" % (self.plugin_name), name, value)

	def get_config_value(self, name):
		return config.get("plugin_%s" % (self.plugin_name), name)

def strip_suffix(filename):
	""" foo.py -> foo """
	return os.path.split(filename)[-1].split(".")[0]

def _register_plugin(filename, modname, module, instance):
	global _plugins
	if _plugins.has_key(filename):
		return False
	_plugins[filename] = (modname, module, instance)
	return True

def _unregister_plugin(filename):
	global _plugins
	if not _plugins.has_key(filename):
		return False
	del _plugins[filename]
	return True

def load(filename):
	global _plugins

	def _unload(name):
		""" unload the module loaded by imp.load_module """
		del sys.modules[name]

	if _plugins.has_key(filename):
		errorMessage("A plugin with that name is already loaded.")
		return False

	# get the name of the module to search for
	name = strip_suffix(filename)

	modInfo = None
	try:
		mod_info = imp.find_module(
			name, config.get_list("tekka","plugin_dir"))

	except ImportError, e:
		errorMessage("Error while finding module for '%s'" % (filename))
		return False

	if not mod_info:
		errorMessage("No plugin found for filename '%s'" % (filename))
		return False

	plugin = None
	modname = _module_prefix + name

	try:
		plugin = imp.load_module(modname, *mod_info)

	except ImportError,e:
		errorMessage("Failure while loading plugin '%s': " % (name), e)

	try:
		mod_info[0].close()
	except (IndexError,AttributeError):
		pass

	if not plugin:
		_unload(modname)
		return False

	try:
		instance = eval ("plugin.%s(PluginInterface())" % (name))

	except BaseException,e:
		errorMessage("Error while instancing plugin: %s" % (e))
		_unload(modname)
		return False

	if not _register_plugin(filename, modname, plugin, instance):
		_unload(modname)

def unload(filename):
	global _plugins

	try:
		entry = _plugins[filename]
	except KeyError:
		errorMessage("Failed to unload plugin '%s', does not exist." % (filename))
		return False

	# tell the instance, it's time to go
	try:
		entry[2].unload()
	except:
		pass

	# "unload" the module
	del sys.modules[entry[0]]

	# unregister locally
	return _unregister_plugin(filename)
