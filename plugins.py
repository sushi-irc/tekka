import sys
import imp
import config
import com
import commands

gui = None
pluginPaths = []
plugins = {}

class sushiPluginHandler(object):
	"""
	interface connecting dbus and plugins.
	"""

	def __init__(self, plugin, sushi):
		"""
			plugin: the name of the plugin receiving the instance of the class
			sushi: dbus.Interface connected to de.ikkoku.sushi
		"""
		self._plugin = plugin
		self._sushi = sushi

	def _check(self, handler, *args):
		"""
			Forwards args to handler if the plugin
			is permitted to receive signals (loaded and enabled).
		"""
		if plugins.has_key(self._plugin) and plugins[self._plugin]["enabled"]:
			handler(*args)

	def connect_to_signal(self, signal, handler):
		"""
			tries to associate signal with handler.
			it adds a check function "over" handler
			which checks every time it was called if
			the plugin is permitted to receive the
			data (=> plugin enabled yes/no).
		"""
		try:
			plugins[self._plugin]["signals"].index(signal)
		except ValueError:
			self._sushi.connect_to_signal(signal, lambda *x: self._check(handler,*x))
			plugins[self._plugin]["signals"].append(signal)
		else:
			# already connected
			return False

	def __getattr__(self, member):
		if member.startswith('__') and member.endswith('__'):
			raise AttributeError(member)
		else:
			return self._sushi.get_dbus_member(member)


"""
	Plugin-API
"""

def getDBusInterface(name):
	"""
		Return a sushiPluginHandler instance.
	"""
	if not plugins.has_key(name):
		return

	if not plugins[name]["proxy"]:
		plugins[name]["proxy"] = sushiPluginHandler(name, com.sushi)
	return plugins[name]["proxy"]

def getGUI():
	return gui

def registerCommand(name, command, fun):
	"""
		Registers a command associated with fun
		in commands and for plugin `name`.
	"""
	if not plugins.has_key(name):
		# the plugin is not active, return
		return False
	
	plugins[name]["commands"].append(command)

	return commands.addCommand(command, fun)

def setPluginOption(name, option, value):
	"""
		set config value for plugin `name`.
		On successful setting the method returns True,
		otherwise False.
	"""
	config.createSection(name)
	return config.set(name, option, value)

def getPluginOption(name, option):
	"""
		get config value for plugin `name`.
		if the option is not found an empty string
		is returned
	"""
	return config.get(name, option, "")

"""
	Methods for plugin stuff.
"""

def _registerPlugin(name, plugin):
	"""
		Registers the plugin in a global dict.
		Only loaded plugins would be registered.
	"""
	global plugins

	if plugins.has_key(name) and plugins[name]["filename"] == filename:
		print "double plugin '%s'!" % (name)
		return False

	plugins[name]={
		"plugin":plugin,
		"commands":[],
		"signals":[],
		"proxy":None,
		"enabled":True
		}

	return True

def _setupPlugin(name, plugin):
	"""
		sets the functions the plugin can use.
	"""	
	# give the plugin the methods it deserves :)
	plugin.getDBusInterface = lambda: getDBusInterface(name)
	plugin.registerCommand = lambda c,f: registerCommand(name, c, f)
	plugin.setOption = lambda o,v: setPluginOption(name, o, v)
	plugin.getOption = lambda o: getPluginOption(name, o)

	plugin.getGUI = getGUI

def loadPlugin(name):
	"""
		searches for a module named like `name` in
		pluginPaths. If a suitable module was found,
		load it, set the plugin-API-methods to the
		module and register it in global dict `plugins`.
		Then call the __init__ function in the module.

		If a plugin was already loaded (plugins[name] exists)
		reload the module and change "enabled" flag to True.
	"""
	if not pluginPaths:
		print "No search paths."
		return

	global plugins

	if plugins.has_key(name):
		print "Module already existing. Enabling."

		data = plugins[name]

		# perform a reload of the module
		data["plugin"] = reload(data["plugin"])
		data["enabled"] = True

		_setupPlugin(name, data["plugin"])
		
		return

	# search for plugin in plugin path

	oldPath = sys.path
	sys.path = pluginPaths

	modTuple = None
	try:
		modTuple = imp.find_module(name)
	except ImportError, e:
		print "E: ", e
		pass

	if not modTuple:
		print "no such plugin found '%s'" % (name)
		sys.path = oldPath
		return

	try:
		plugin = imp.load_module(name, *modTuple)
	except ImportError:
		print "Failure while loading plugin '%s'" % (name)
	finally:
		try:
			modTuple[0].close()
		except (IndexError,AttributeError):
			pass

	# reset old search path
	sys.path = oldPath

	if not _registerPlugin(name, plugin):
		# registration failed, abort loading..
		print "registration failed."
		return

	_setupPlugin(name, plugin)

	plugin.__init__()

def unloadPlugin(name):
	"""
		removes the plugin (refcount = 0).
		Before the deletion is made, __destruct__
		is called in the module.
	"""
	global plugins

	if not plugins.has_key(name):
		print "no such plugin registered ('%s')"
		return False

	try:
		plugins[name].__destruct__()
	except AttributeError:
		pass


	# try to unregister all commands created by the plugin
	try:
		for command in plugins[name]["commands"]:
			commands.removeCommand(command)
	except KeyError:
		pass

	# because modules are not deletable, make it unuseable
	# and set it to enabled = False

	plugins[name]["plugin"].getDBusInterface = None
	plugins[name]["plugin"].registerCommand = None
	plugins[name]["plugin"].setOption = None
	plugins[name]["plugin"].getOption = None
	plugins[name]["plugin"].getGUI = None
	plugins[name]["enabled"] = False
	# NOTE:  important: do NOT delete the entry in plugins!
	# NOTE:: If you do this all signal entries will be lost
	# NOTE:: so they will be added the next time the plugin
	# NOTE:: is initalized.

def setup(_gui):
	"""
		module setup function.
	"""
	global gui, pluginPaths

	gui = _gui

	# TODO: make multiple plugin paths possible
	path = config.get("tekka", "plugin_dir", default="")

	if not path: return

	pluginPaths.append(path)
