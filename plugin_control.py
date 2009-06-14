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
from gettext import gettext as _

import com
import commands
import signals
import config

_module_prefix = "tekkaplugin_"
_plugins = {}

(
	PLUGIN_MODNAME,
	PLUGIN_MODULE,
	PLUGIN_INSTANCE,
	PLUGIN_INFO_LENGTH
) = range(4)

def generic_error(primary, secondary):
	d = gui_control.InlineMessageDialog(primary, secondary)
	gui_control.showInlineDialog(d)
	d.connect("response", lambda d,i: d.destroy())

def strip_suffix(filename):
	""" foo.py -> foo """
	return os.path.split(filename)[-1].split(".")[0]

def is_loaded(filename):
	""" returns True if the plugin is loaded, otherwise False """
	return _plugins.has_key(filename)

def _register_plugin(filename, modname, module, instance):
	""" add plugin to local plugin dict, key is filename """
	global _plugins
	if _plugins.has_key(filename):
		return False
	_plugins[filename] = (modname, module, instance)
	return True

def _unregister_plugin(filename):
	""" remove plugin from local plugin dict """
	global _plugins
	if not _plugins.has_key(filename):
		return False
	del _plugins[filename]
	return True

def _find_module(filename):
	""" wrapper for imp.find_module.
		Searches for the module named after
		filename in the configured search
		path (tekka, plugin_dirs).
	"""
	# get the name of the module to search for
	name = strip_suffix(filename)

	mod_info = None
	try:
		mod_info = imp.find_module(
			name, config.get_list("tekka","plugin_dirs"))

	except ImportError, e:
		generic_error(_("Plugin not found:"), _("Error while finding module for '%s'" % (filename)))
		return None

	if not mod_info:
		generic_error(_("Plugin not found:"), _("No plugin found for filename '%s'" % (filename)))
		return None

	return mod_info

def _load_module(filename, mod_info):
	""" wrapper for imp.load_module.
		Returns a tuple with the identifying
		name of the loaded module and the
		module itself if loading was successful.
		Otherwise the function returns (None,None).
	"""
	name = strip_suffix(filename)
	plugin = None
	modname = _module_prefix + name

	try:
		plugin = imp.load_module(modname, *mod_info)

	except ImportError,e:
		generic_error(_("Plugin load failed:"), _("Failure while loading plugin '%s': %s" % (name, e)))

	try:
		mod_info[0].close()
	except (IndexError,AttributeError):
		pass

	return modname, plugin

def _unload_module(name):
	""" unload the module loaded by imp.load_module
		by deleting it's reference from sys.modules
	"""
	del sys.modules[name]


def load(filename):
	""" load a module named after filename in the
		configured search path (tekka, plugin_dirs),
		instance the class named after the module
		(np for np.py) and register the bunch.

		On error this function calls generic_error()
		with an specific error message and returns
		False. Otherwise this function returns True.
	"""
	global _plugins

	if _plugins.has_key(filename):
		generic_error(_("Plugin already loaded."), _("A plugin with that name is already loaded."))
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
		instance = eval ("plugin.%s()" % (classname))

	except BaseException,e:
		generic_error(_("Plugin load failed:"), _("Error while instancing plugin: %s" % (e)))
		_unload_module(modname)
		return False

	if not _register_plugin(filename, modname, plugin, instance):
		_unload_module(modname)
		return False
	return True

def unload(filename):
	""" Call unload() in the plugin instance,
		unload the module and unregister it.
		On success this function returns True,
		otherwise it returns False.
	"""
	global _plugins

	try:
		entry = _plugins[filename]
	except KeyError:
		generic_error(_("Plugin unload failed:"), _("Failed to unload plugin '%s', does not exist." % (filename)))
		return False

	# tell the instance, it's time to go
	try:
		entry[PLUGIN_INSTANCE].unload()
	except:
		pass

	_unload_module(entry[PLUGIN_MODNAME])

	# unregister locally
	return _unregister_plugin(filename)

def _check_info_tuple(info):
	if (type(info) != tuple
		or len(info) != PLUGIN_INFO_LENGTH
		or len([n for n in info if type(n) != str])):
		return False
	return True

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
			info = _plugins[filename][PLUGIN_MODULE].plugin_info
		except:
			return None

		if not _check_info_tuple(info):
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
		if not _check_info_tuple(info):
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
			generic_error(_("Plugin load failed:"),
				_("Failed to load plugin '%s' automatically, removing from list." % (filename)))
			config.unset("autoload_plugins",opt)

