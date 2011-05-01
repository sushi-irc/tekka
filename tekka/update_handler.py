"""
Handler for updates between revisions and versions.
"""

import gobject
import logging

from . import gui

def message_success(user_data):
	(title, message) = user_data
	gui.mgmt.show_inline_message(title, message)

def message_failure(user_data):
	(title, message) = user_data
	gui.mgmt.show_inline_message(title, message, dtype="error")


def json_get_list_update():
	" get_list internals were replaced by json parsing, updates config "

	from . import config
	from .helper import escape

	if config.get_bool("updates", "json_config"):
		return

	logging.info("json_get_list_update starting.")

	changes = 0

	for section in config.config_parser.sections():
		for (name, value) in config.config_parser.items(section):
			if value.count(",") > 1 and value[0] != "[": # got old list
				# convert to list via old stuff
				l = escape.unescape_split(",", value)
				config.set_list(section, name, l)

				changes += 1

				logging.info("Updated option %s from %s to %s" % (
					name, value, config.get_list(section, name, [])))

	logging.info("json_get_list_update done: %d changes." % (changes,))

	config.set_bool("updates", "json_config", True)

	gobject.idle_add(message_success, ("Update succeeded",
		"The config update was successfuly applied."))
