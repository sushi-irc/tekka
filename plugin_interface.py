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

PLUGIN_MODNAME=0
PLUGIN_MODULE=1
PLUGIN_INSTANCE=2

class PluginInterface(gobject.GObject):

	def __init__(self, plugin_name):
		self._plugin_name = plugin_name

	def get_dbus(self):
		return com.sushi

	def add_command(self, command, func):
#		self.emit("command_add", command, func)
		return commands.addCommand(command, func)

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
		config.create_section("plugin_%s" % (self.plugin_name))
		return config.set("plugin_%s" % (self.plugin_name), name, value)

	def get_config_value(self, name):
		return config.get("plugin_%s" % (self.plugin_name), name)

def strip_suffix(filename):
	""" foo.py -> foo """
	return os.path.split(filename)[-1].split(".")[0]

def is_loaded(filename):
	return _plugins.has_key(filename)

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

def _find_module(filename):
	# get the name of the module to search for
	name = strip_suffix(filename)

	mod_info = None
	try:
		mod_info = imp.find_module(
			name, config.get_list("tekka","plugin_dirs"))

	except ImportError, e:
		errorMessage("Error while finding module for '%s'" % (filename))
		return None

	if not mod_info:
		errorMessage("No plugin found for filename '%s'" % (filename))
		return None

	return mod_info

def _load_module(filename, mod_info):
	name = strip_suffix(filename)
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

	return modname, plugin

def _unload_module(name):
	""" unload the module loaded by imp.load_module """
	del sys.modules[name]


def load(filename):
	global _plugins

	if _plugins.has_key(filename):
		errorMessage("A plugin with that name is already loaded.")
		return False

	mod_info = _find_module(filename)

	if not mod_info:
		return False

	modname, plugin = _load_module(filename, mod_info)
	classname = strip_suffix(filename)

	if not plugin:
		_unload_module(modname)
		return False

	try:
		instance = eval ("plugin.%s(PluginInterface('%s'))" % (classname, filename))

	except BaseException,e:
		errorMessage("Error while instancing plugin: %s" % (e))
		_unload_module(modname)
		return False

	if not _register_plugin(filename, modname, plugin, instance):
		_unload_module(modname)
		return False
	return True

def unload(filename):
	global _plugins

	try:
		entry = _plugins[filename]
	except KeyError:
		errorMessage("Failed to unload plugin '%s', does not exist." % (filename))
		return False

	# tell the instance, it's time to go
	try:
		entry[PLUGIN_INSTANCE].unload()
	except:
		pass

	_unload_module(entry[PLUGIN_MODNAME])

	# unregister locally
	return _unregister_plugin(filename)

def get_info(filename):
	""" return the plugin info from the plugin.
		If any error occurs, this function
		returns None, else it returns a tuple.

		tuple returned:
		(<description>, <version>, <author>)
	"""
	global _plugins

	if _plugins.has_key(filename):
		try:
			info = _plugins[filename][PLUGIN_INSTANCE].plugin_info()
		except:
			return None

		if type(info) != tuple or len(info) != 2:
			return None
		return info
	else:
		name = strip_suffix(filename)
		mod_info = _find_module(filename)

		if not mod_info:
			return None

		modname, plugin = _load_module(filename, mod_info)

		if not plugin:
			return None

		try:
			info = plugin.plugin_info
		except AttributeError:
			_unload_module(modname)
			return None

		# return None if the attribute is not a tuple
		# or any item in the tuple is not a string
		if (type(info) != tuple
			or len(info) != 3
			or len([n for n in info if type(n) != str])):
			_unload_module(modname)
			return None

		_unload_module(modname)

		return info

	return None

def load_autoloads():
	autoloads = config.get("autoload_plugins").items()
	for opt,filename in autoloads:
		print "autoloading '%s'" % (filename)
		if not load(filename):
			errorMessage("Failed to load plugin '%s' automatically, "\
				"removing from list." % (filename))
			config.unset("autoload_plugins",opt)

