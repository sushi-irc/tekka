import imp

config = None

pluginPaths = []

def setup(_config):
	"""
		...
	"""
	global config, pluginPaths

	config = _config

	pluginPaths = config.get("tekka","pluginPath",default=[])

def loadPlugin(name):
	"""
		...
	"""
	for path in pluginPaths:
		modTuple = None
		try:
			modTuple = imp.find_module(name, path)
		except ImportError:
			continue

	if not modTuple:
		return

	try:
		plugin = load_module(name, *modTuple)
	except ImportError:
		print "Failure while loading plugin '%s'" % (name)
	finally:
		try:
			modTuple[0].close()
		except (IndexError,AttributeError):
			pass

	# TODO: further stuff
