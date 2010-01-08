import gtk

from . import widgets
from .. import config
from ..helper import shortcuts

_accelGroup = gtk.AccelGroup()
_handlers = {
		"clear_outputs": [],
		"output_page_up": [],
		"output_page_down": [],
		"input_clear_line": [],
		"input_search": [],
		"input_search_further": [],
		"input_copy": [],
		"servertree_previous": [],
		"servertree_next": [],
		"servertree_close": [],
		"show_sidepane": []
	}

def add_handlers(d):
	global _handlers

	for (key, val) in d.items():
		if _handlers.has_key(key):
			_handlers[key].append(val)

def get_shortcut_handler(shortcut):
	global _handlers

	try:
		return _handlers[shortcut]
	except KeyError:
		return None

def associate_handler(short_name, shortcut, widget):
	global _handlers

	try:
		for handler in _handlers[short_name]:
			shortcuts.addShortcut(
				_accelGroup,
				widgets.get_widget(widget),
				shortcut,
				handler)

	except KeyError:
		pass

def setup_shortcuts():
	"""
		Set shortcuts to widgets.

		- ctrl + page_up -> scroll to prev tab in server tree
		- ctrl + page_down -> scroll to next tab in server tree
		- ctrl + w -> close the current tab
		- ctrl + l -> clear the output buffer
		- ctrl + u -> clear the input entry
		- ctrl + s -> hide/show the side pane
	"""
	global _accelGroup

	widgets.get_widget("mainWindow").add_accel_group(_accelGroup)

	associate_handler("clear_outputs", "<ctrl>l", "inputBar")

	associate_handler("input_clear_line", "<ctrl>u", "inputBar")
	associate_handler("input_search", "<ctrl>f", "inputBar")
	associate_handler("input_search_further", "<ctrl>g", "inputBar")
	associate_handler("input_copy", "<ctrl>c", "inputBar")

	associate_handler("servertree_previous", "<ctrl>Page_Up", "serverTree")
	associate_handler("servertree_next", "<ctrl>Page_Down", "serverTree")
	associate_handler("servertree_close", "<ctrl>w", "serverTree")

	associate_handler("output_page_up", "Page_Up", "inputBar")
	associate_handler("output_page_down", "Page_Down", "inputBar")

	associate_handler("show_sidepane", "<ctrl>s", "menu_View_showSidePane")


def assign_numeric_tab_shortcuts(tabList):
	""" assign numeric shortcuts (alt+N) for each
		tab in the list tabs.
	"""
	global _accelGroup

	st = widgets.get_widget("serverTree")

	for i in range(1, 10):
		shortcuts.removeShortcut(_accelGroup, st, "<alt>%d" % (i))

	c = 1
	for tab in tabList:
		if c == 10:
			break

		if (tab.is_server()
		and not config.get("tekka", "server_shortcuts")):
			continue

		shortcuts.addShortcut(_accelGroup, st, "<alt>%d" % (c),
			lambda w, s, p: p.switch_to(), tab)

		c+=1


