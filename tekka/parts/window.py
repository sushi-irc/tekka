from .. import gui
from .. import config

import gtk
import gobject


def setup(tekka):
	setup_main_window()
	return Window(tekka)


class Window(object):

	def __init__(self, tekka):
		pass


	def test(self):
		return True


	def widget_signals(self):
		return {
			# main window signals
			"main_window_delete_event":
				mainWindow_delete_event_cb,
			"main_window_focus_in_event":
				mainWindow_focus_in_event_cb,
			"main_window_size_allocate":
				mainWindow_size_allocate_cb,
			"main_window_window_state_event":
				mainWindow_window_state_event_cb,
			"main_window_scroll_event":
				mainWindow_scroll_event_cb,
		}




def setup_main_window():
	"""
		- set window title
		- set window icon
		- set window size
		- set window state
	"""
	win = gui.widgets.get_object("main_window")

	win.set_title("tekka IRC client")

	if config.get_bool("tekka", "rgba"):
		colormap = win.get_screen().get_rgba_colormap()
		if colormap:
			gtk.widget_set_default_colormap(colormap)

	try:
		img = gtk.icon_theme_get_default().load_icon("tekka",64,0)

		win.set_icon(img)
	except gobject.GError:
		# file not found
		pass

	# Restore sizes from last start
	width = config.get("sizes","window_width")
	height = config.get("sizes","window_height")

	if width and height:
		win.resize(int(width),int(height))


	# Restore window state from last start
	if config.get_bool("tekka","window_maximized"):
		win.maximize()

	# enable scrolling through server tree by scroll wheel
	def kill_mod1_scroll(w,e):
		if e.state & gtk.gdk.MOD1_MASK:
			w.emit_stop_by_name("scroll-event")

	for widget in ("general_output_window",
				   "tabs_window",
				   "nicks_window"):
		gui.widgets.get_object(widget).connect("scroll-event",
											   kill_mod1_scroll)

	win.show()




def mainWindow_scroll_event_cb(mainWindow, event):
	""" MOD1 + SCROLL_DOWN -> Next tab
		MOD1 + SCROLL_UP -> Prev. tab
	"""

	if (event.state & gtk.gdk.MOD1_MASK
	and event.direction == gtk.gdk.SCROLL_DOWN):
		gui.tabs.switch_to_next()

	elif (event.state & gtk.gdk.MOD1_MASK
	and event.direction == gtk.gdk.SCROLL_UP):
		gui.tabs.switch_to_previous()



def mainWindow_delete_event_cb(mainWindow, event):
	"""
		If hide_on_close and the status icon are enabled,
		hide the main window. Otherwise stop the main loop.

		On hide, a read-line will be inserted in every tab.
	"""

	statusIcon = gui.widgets.get_object("status_icon")

	if (config.get_bool("tekka", "hide_on_close")
	and statusIcon and statusIcon.get_visible()):

		for tab in gui.tabs.get_all_tabs():
			tab.window.textview.set_read_line()

		mainWindow.hide()

		return True

	else:
		gtk.main_quit()



def mainWindow_focus_in_event_cb(mainWindow, event):
	"""
		Reset urgent status (if given)
	"""

	gui.mgmt.set_urgent(False)
	return False


def mainWindow_size_allocate_cb(mainWindow, alloc):
	""" Main window was resized, store the new size in the config. """

	if not mainWindow.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("sizes","window_width",alloc.width)
		config.set("sizes","window_height",alloc.height)


def mainWindow_window_state_event_cb(mainWindow, event):
	""" Window state was changed.
		If it's maximized or unmaximized, save that state.
	"""

	if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("tekka","window_maximized","True")
	else:
		config.set("tekka","window_maximized","False")



