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
import logging

# lists are parsed via json
import json

from xdg.BaseDirectory import xdg_config_home, xdg_data_home, \
	xdg_cache_home
import ConfigParser

from .lib import contrast

from .typecheck import types
from .helper.escape import unescape_split, escape_join

from . import update_handler

prefix = ""
defaults = {}

config_parser = None
config_file = ""

encoder = json.JSONEncoder()
decoder = json.JSONDecoder()

_watcher = {}

update_handler = [update_handler.json_get_list_update]

def get_path(*c):
	return os.path.abspath(os.path.join(prefix, *c))

def set_defaults():
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
		API. For example the section "uifiles".
	"""
	global defaults

	defaults = {}

	defaults["tekka"] = {}
	defaults["tekka"]["logfile"] = os.path.join(xdg_cache_home, "sushi",
		"tekka.txt")
	defaults["tekka"]["locale_dir"] = get_path("..", "..", "locale")
	defaults["tekka"]["plugin_dirs"] = '["' + '","'.join((
			os.path.join(xdg_data_home, "tekka", "plugins"),
			os.path.join(xdg_data_home, "sushi", "plugins"),
			get_path("plugins"),
			get_path("..", "plugins")
		)) + '"]'
	defaults["tekka"]["use_default_font"] = "True"
	defaults["tekka"]["font"] = "Monospace 10"
	defaults["tekka"]["auto_expand"] = "True"
	defaults["tekka"]["smooth_scrolling"] = "False"
	defaults["tekka"]["idialog_timeout"] = "False"
	defaults["tekka"]["idialog_timeout_seconds"] = "5"

	defaults["tekka"]["show_general_output"] = "True"
	defaults["tekka"]["show_topic_bar"] = "False"
	defaults["tekka"]["hide_topic_if_empty"] = "True"
	defaults["tekka"]["show_side_pane"] = "True"
	defaults["tekka"]["show_status_bar"] = "True"

	defaults["tekka"]["rgba"] = "False"
	defaults["tekka"]["close_maki_on_close"] = "False"
	defaults["tekka"]["color_text"] = "True" 		# colors enabled?
	defaults["tekka"]["color_nick_text"] = "False" 	# color the text as well as the nick
	defaults["tekka"]["ask_for_key_on_cannotjoin"] = "True"
	defaults["tekka"]["switch_to_channel_after_join"] = "True"

	defaults["tekka"]["whois_dialog"] = "True"      # pop up a dialog on /whois?
	defaults["tekka"]["divider_length"] = "30"      # how much spaces one divider has
	defaults["tekka"]["max_output_lines"] = "500"   # max. lines in one output window
	defaults["tekka"]["profiling"] = "False"        # performance profiling switch
	defaults["tekka"]["popup_line_limit"] = "10"
	defaults["tekka"]["names_columns"] = "5"        # nicks in one row in /names output
	defaults["tekka"]["browser"] = None
	defaults["tekka"]["text_rules"] = "True"
	defaults["tekka"]["rules_limit"] = "3"


	defaults["dcc"] = {}
	defaults["dcc"]["show_ident_in_dialog"] = "False"

	defaults["general_output"] = {}
	defaults["general_output"]["valid_types"] = '["message","action","highlightmessage","highlightaction"]'
	defaults["general_output"]["filter"] = ""
	"""
	filter take place here.
	'type == "message" and server == "euIRC" and channel == "#bsdunix"'
	'not (type == "action" and server == "Freenode" and channel == "#sushi-irc")'
	"""

	defaults["sizes"] = {}
	defaults["sizes"]["outputVPaned"] = "150"
	"""
	[window_height]
	[window_width]
	[$(paned)] = <paned position>
	"""

	defaults["colors"]={}
	defaults["colors"]["own_nick"] = str(contrast.CONTRAST_COLOR_GREY)
	defaults["colors"]["own_text"] = str(contrast.CONTRAST_COLOR_GREY)
	defaults["colors"]["notification"] = str(contrast.CONTRAST_COLOR_LIGHT_GREY)
	defaults["colors"]["text_message"] = str(contrast.CONTRAST_COLOR_BLACK)
	defaults["colors"]["text_action"] = str(contrast.CONTRAST_COLOR_BLACK)
	defaults["colors"]["text_highlightmessage"] = str(contrast.CONTRAST_COLOR_RED)
	defaults["colors"]["text_highlightaction"] = str(contrast.CONTRAST_COLOR_RED)
	defaults["colors"]["nick"] = str(contrast.CONTRAST_COLOR_GREEN) # default foreign nick color
	defaults["colors"]["last_log"] = str(contrast.CONTRAST_COLOR_LIGHT_GREY)

	defaults["colors"]["nick_contrast_colors"] = "True"
	defaults["colors"]["nick_colors"] = '["#AA0000","#2222AA","#44AA44","#123456","#987654"]'
	defaults["colors"]["rules_color"] = "auto" # color for htmlbuffer ruling
	defaults["colors"]["irc_colors"] = "True" # display IRC colors (\003X,Y)
	# markup colors
	defaults["colors"]["new_message"] = str(contrast.CONTRAST_COLOR_LIGHT_BROWN)
	defaults["colors"]["new_action"] = str(contrast.CONTRAST_COLOR_LIGHT_BROWN)
	defaults["colors"]["new_highlightmessage"] = str(contrast.CONTRAST_COLOR_DARK_RED)
	defaults["colors"]["new_highlightaction"] = str(contrast.CONTRAST_COLOR_DARK_GREEN)
	defaults["colors"]["color_new_messages"] = "False"

	defaults["chatting"]={}
	defaults["chatting"]["last_log_lines"] = "10"
	defaults["chatting"]["quit_message"] = "Leading."
	defaults["chatting"]["part_message"] = "Partitioning."
	defaults["chatting"]["nick_separator"] = ": "
	defaults["chatting"]["time_format"] = "%H:%M"
	defaults["chatting"]["highlight_words"] = "[]"

	defaults["autoload_plugins"] = {}

	# section for update handler specific options
	defaults["updates"]={}

	# Add default sections to config parser
	# so setting is easier
	for section in defaults.keys():
		try:
			config_parser.add_section(section)
		except ConfigParser.DuplicateSectionError:
			continue

	# sections defined below are not added to the configParser and
	# can't be set by the set method (will raise NoSectionError)
	defaults["uifiles"] = {}
	defaults["uifiles"]["mainwindow"] = get_path("ui", "main_window.ui")
	defaults["uifiles"]["menus"] = get_path("ui", "menus") + os.path.sep
	defaults["uifiles"]["dialogs"] = get_path("ui", "dialogs") + os.path.sep



def read_config_file():
	"""
	Reads the config file.
	"""
	success = config_parser.read([config_file])

	if not success:
		print "Failed to parse config file '%s'" % config_file
		return False

	return True

def write_config_file():
	"""
	Writes the config values from the
	ConfigParser object into the given file (config_file)
	"""
	if not config_parser:
		logging.error("Config module not loaded. I don't save anything.")
		return

	# remove empty sections so the won't be written
	for section in config_parser.sections():
		if len(config_parser.items(section)) == 0:
			config_parser.remove_section(section)

	f = file(config_file, "w")
	config_parser.write(f)
	f.close()

@types(section=basestring, user_data=tuple)
def add_watcher(section, value, callback, user_data=()):
	""" add watcher to listen for changes on a variable """
	if _watcher.has_key(section):
		if _watcher.has_key(value):
			_watcher[section][value][callback] = user_data
		else:
			_watcher[section][value] = {callback:user_data}
	else:
		_watcher[section] = {value:{callback:user_data}}

def remove_watcher(section, value, callback):
	""" remove a watcher (callback) for this section/value """
	try:
		l = _watcher[section][value]
		i = l.index(callback)
		del l[i]
		return True
	except ValueError, KeyError:
		return False

def _call_watcher(section, value):
	""" call registered watcher for section and value """
	try:
		w = _watcher[section][value]
	except KeyError:
		return
	for (callback,args) in w:
		watcher(section, value, *args)

@types (section = basestring)
def has_section(section):
	return config_parser.has_section(section)

@types (section=basestring)
def create_section(section):
	"""
		creates config section `section`.
	"""
	if not config_parser or config_parser.has_section(section):
		return False
	config_parser.add_section(section)
	return True

@types (section=basestring)
def remove_section(section):
	"""
		removes the section
	"""
	if not config_parser or not config_parser.has_section(section):
		return False

	config_parser.remove_section(section)
	return True

@types (section=basestring, option=basestring)
#@on_fail (print_debug, "ConfigError while setting %s:%s to %s")
def set(section, option, value):
	"""
		Sets in the section the option to value.
		On success the method returns True.
	"""
	if not config_parser:
		return False

	# TODO: enable, test, stuff
	#_call_watcher(section, option)

	try:
		config_parser.set(section, option, str(value))
	except ConfigParser.NoSectionError:
		return False
	else:
		return True

@types(section=basestring, option=basestring, value=bool)
def set_bool(section, option, value):
	return set(section, option, str(value))

@types (section=basestring, option=basestring, l=list)
def set_list(section, option, l):
	""" Set the content of l as value of option.
		Lists are saved in a JSON parseable format.
	"""
	s = encoder.encode(l)

	return set(section, option, s)

@types (section=basestring, option=basestring, value=basestring)
def append_list(section, option, value):
	""" Add value to the list identified by option """
	v = get_list(section, option, [])
	v.append(value)
	return set_list(section, option, v)

@types (section=basestring, option=basestring)
def unset(section, option):
	""" Removes the option in the section.
		Returns True on success otherwise False.
	"""
	if not config_parser:
		return False
	try:
		config_parser.remove_option(section, option)
	except ConfigParser.NoSectionError,e:
		print "Unsetting ('%s','%s') failed: %s" % (section,option,e)
		return False
	return True

@types (section=basestring, option=basestring)
def get(section, option="", default=None):
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

	if not config_parser:
		return default

	if not option:
		# get the whole section

		if config_parser.has_section(section):
			# the section is noticed by the parser,
			# merge with defaults (if any) and return
			# the value-dict

			new = dict(config_parser.items(section))

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
			return config_parser.get(section, option)
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

@types (section=basestring, option=basestring)
def get_list(section, option, default):
	"""
		Splits the option in the section for ","
		and returns a list if the splitting was
		successful. Else the method will return
		"default".

		Notice: If there's an empty string set,
		this function will return default.
	"""
	res = get(section, option, default)

	if res == default or not res:
		return default

	l = decoder.decode(res)

	if l == default or not l:
		return default
	return l

@types (section=basestring, option=basestring)
def get_bool(section, option, default=False):
	"""
		Returns True or False if the value is
		set or unset.
	"""
	res = get(section, option, default)

	if res == default:
		return default

	if res.lower() == "true" or res == "1":
		return True

	return default

@types (section=basestring, option=basestring)
def get_default(section, option=""):
	"""
	Returns the default value for the option
	in the given section. If no option is given
	(option = None) all defaults of the given
	section are returned as a dictionary.
	If there are no defaults, None is returned.
	"""
	if not option:
		if defaults.has_key(section):
			return defaults[section]
	else:
		if defaults.has_key(section):
			if defaults[section].has_key(option):
				return str(defaults[section][option])
	return None

def is_default(section, option):
	""" check if the value of the option matches the default value
		for the option in the section.
	"""
	return get_default(section,option) == get(section,option)

def reset_value(section, option):
	set(section, option, get_default(section, option))

@types (path=basestring)
def check_config_file(path):
	""" check if config file exists and create it if not """
	if not os.path.exists (path):
		# create the directories
		try:
			os.makedirs (os.path.join (os.path.split (path)[0]))
		except os.error:
			print "Error while creating neccessary directories: %s"\
				% (os.error)
			return False

		try:
			f = file (path, "w")
		except BaseException as e:
			print "Error while creating config file: %s" % (e)
			return False
		else:
			f.close()

		return True
	else:
		return True
	return False

def setup():
	"""
	Find the usual location of the config dir
	(XDG_CONFIG_HOME/sushi/tekka) and parse the
	config file if found.
	"""
	global config_parser, config_file
	global prefix


	if os.path.islink(sys.argv[0]):
		link = os.readlink(sys.argv[0])

		if not os.path.isabs(link):
			link = os.path.join(os.path.dirname(sys.argv[0]), link)

		prefix = os.path.dirname(os.path.abspath(link))
	else:
		prefix = os.path.dirname(os.path.abspath(sys.argv[0]))

	config_parser = ConfigParser.ConfigParser()
	set_defaults()

	config_file = os.path.join (xdg_config_home, "sushi", "tekka")

	if not check_config_file(config_file):
		print "Config file creation failed. Aborting."
		return

	read_config_file()

	for handler in update_handler:
		handler()


