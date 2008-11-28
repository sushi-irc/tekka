# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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
	defaults["tekka"]["rgba"] = "False"
	defaults["tekka"]["color_text"] = "True" 		# colors enabled?
	defaults["tekka"]["color_nick_text"] = "False" 	# color the text as well as the nick

	defaults["colors"]={}
	defaults["colors"]["own_nick"] = "#444444"
	defaults["colors"]["own_text"] = "#444444"
	defaults["colors"]["notification"] = "#AAAAAA"
	defaults["colors"]["text_message"] = "#000000"
	defaults["colors"]["text_action"] = "#BBBBBB"
	defaults["colors"]["text_highlightmessage"] = "#FF0000"
	defaults["colors"]["text_highlightaction"] = "#0000FF"
	defaults["colors"]["nick"] = "#2222AA" # default foreign nick color

	defaults["chatting"]={}
	defaults["chatting"]["last_log_lines"] = "10"
	defaults["chatting"]["quit_message"] = "default quit message"
	defaults["chatting"]["part_message"] = "default part message"

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
		link = os.readlink(sys.argv[0])

		if not os.path.isabs(link):
			link = os.path.join(os.path.dirname(sys.argv[0]), link)

		prefix = os.path.dirname(os.path.abspath(link))
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
