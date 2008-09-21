import os
import sys

from xdg.BaseDirectory import xdg_config_home
import ConfigParser

prefix = ""
defaults = {}

configParser = None
configFile = ""

def setDefaults():
	"""
		Sets the default values.

		I know that the ConfigParser class has a
		method to set defaults but these defaults
		are global and not bound to a section.
		If you want a default nick color you can
		set it but if you have another option
		with the same name the default value will
		be the same and this sucks.

		A further point is that this way realizes
		"private" values which are not written
		to config files but can be used with the same
		API. For example the section "gladefiles".
	"""
	global defaults

	defaults["tekka"] = {}
	defaults["tekka"]["locale_dir"] = os.path.join(prefix, "..", "..", "locale")
	defaults["tekka"]["status_icon"] = os.path.join(prefix, "graphics", "icon.svg")
	defaults["tekka"]["plugin_dir"] = os.path.join(prefix, "plugins")
	defaults["tekka"]["output_font"] = "Monospace"
	defaults["tekka"]["general_output_font"] = "Monospace"
	defaults["tekka"]["auto_expand"] = "True"
	defaults["tekka"]["show_general_output"] = "True"

	defaults["colors"]={}
	defaults["colors"]["own_nick"] = "#444444"
	defaults["colors"]["own_text"] = "#444444"
	defaults["colors"]["nick"] = "#2222AA"
	defaults["colors"]["join_nick"] = "#004444"
	defaults["colors"]["part_nick"] = "#004444"
	defaults["colors"]["mode_act_nick"] = "#AA2222"
	defaults["colors"]["mode_param"] = "#2222AA"

	defaults["chatting"]={}
	defaults["chatting"]["last_log_lines"] = "10"

	defaults["autoload_plugins"] = {}

	defaults["nick_colors"]={
		"1":"#AA0000",
		"2":"#2222AA",
		"3":"#44AA44",
		"4":"#123456",
		"5":"#987654"
		}

	# Add default sections to config parser
	# so setting is easier
	for section in defaults.keys():
		try:
			configParser.add_section(section)
		except ConfigParser.DuplicateSectionError:
			continue

	# these section is not added to the configParser and
	# can't be set by the set method (will raise NoSectionError)
	defaults["gladefiles"] = {}
	defaults["gladefiles"]["mainwindow"] = os.path.join(prefix, "glade", "mainwindow.glade")
	defaults["gladefiles"]["dialogs"] = os.path.join(prefix, "glade", "dialogs.glade")

def readConfigFile():
	"""
		Reads the config file.
	"""

	success = configParser.read([configFile])

	if not success:
		print "Failed to parse config file '%s'" % configFile
		return False

	return True

def writeConfigFile():
	"""
		Writes the config file.
		Special thanks to Captain Obvious...
	"""
	fp = file(configFile,"w")

	configParser.write(fp)

	fp.close()

def createSection(section):
	"""
		creates config section `section`.
	"""
	if configParser.has_section(section):
		return False
	configParser.add_section(section)
	return True

def set(section, option, value):
	"""
		Sets in the section the option to value.
		On success the method returns True.
	"""
	try:
		configParser.set(section, option, value)
	except ConfigParser.NoSectionError:
		return False
	else:
		return True

def unset(section, option):
	"""
		Removes the option in the section.
		Returns True on success otherwise False.
	"""
	try:
		configParser.remove_option(section, option)
	except Exception:
		return False
	return True

def get(section, option=None, default=None):
	"""
		Returns the value for option in section, on
		error the method returns default.

		If option is not given, the whole section
		is returned as dictionary of type {option:value}.
		If there are default values for the section they
		will be merged in.

		The `option`-value is handled case-insensitive.

		get("tekka") will return {"server_shortcuts":"1"}
		get("tekka","server_shortcuts") will return "1"
		get("tekki") will return default
	"""

	if not option:
		# get the whole section

		if configParser.has_section(section):
			# the section is noticed by the parser,
			# merge with defaults (if any) and return
			# the value-dict

			new = dict(configParser.items(section))

			if defaults.has_key(section):
				# merge defaults + config values together
				copy = defaults[section].copy()
				copy.update(new)
				return copy
			else:
				return new

		elif defaults.has_key(section):
			# the config parser does not know the
			# section but it's found in defaults-dict.
			# This is probably a private section.
			return defaults[section]

		else:
			return default

	else:
		# get specific option

		try:
			return configParser.get(section, option)
		except (ConfigParser.NoOptionError, ConfigParser.NoSectionError),e:
			if defaults.has_key(section):
				try:
					return defaults[section][option]
				except KeyError:
					return default
		else:
			return default

	# usually this is not reached
	return default

def getBool(section, option, default=None):
	"""
		Returns True or False if the value is
		set or unset.
	"""
	res = get(section, option, default)

	if res == default:
		return False

	if res.lower() == "true" or res == "1":
		return True

	return False

def setup():
	"""
		TODO: document
	"""
	global configParser, configFile
	global prefix

	if os.path.islink(sys.argv[0]):
		prefix = os.path.dirname(os.path.abspath(os.readlink(sys.argv[0])))
	else:
		prefix = os.path.dirname(os.path.abspath(sys.argv[0]))

	configParser = ConfigParser.ConfigParser()
	setDefaults()
	configFile = os.path.join(xdg_config_home,"sushi","tekka")

	readConfigFile()


if __name__ == "__main__":
	setup()
	readConfigFile()

	print "Without defaults:"
	for section in configParser.sections():
		print "section '%s':" % (section)
		for (option,value) in configParser.items(section):
			print "\t%s = %s" % (option, value)

	print "With defaults:"

	all={"tekka":("server_shortcuts","localeDir"),"gladefiles":(),"chatting":("lastLogLines",),"nickColors":()}

	for section in configParser.sections():
		print "section '%s':" % (section)
		if all.has_key(section):
			for item in all[section]:
				print "get('%s','%s')" % (section,item)
				print get(section, item)
			else:
				print "dump section '%s'" % (section)
				print get(section)
		else:
			get(section)

	print "private section 'gladefiles':"
	print get("gladefiles")

	print "setting server_shortcuts in section tekka to 1."
	set("tekka","server_shortcuts","1")
	print get("tekka","server_shortcuts")
