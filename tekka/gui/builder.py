import gtk

from ._widgets import widgets, WidgetsWrapper
from .. import gui

from .. import config
from ..typecheck import types

from ..lib.htmlbuffer import HTMLBuffer
from ..lib.general_output_buffer import GOHTMLBuffer
from ..lib.status_icon import TekkaStatusIcon
from ..lib.search_toolbar import SearchBar
from ..lib.output_textview import OutputTextView
from ..lib.output_shell import OutputShell
from ..lib.output_window import OutputWindow
from ..helper import URLHandler

from ..helper.shortcuts import addShortcut

def get_new_buffer():
	""" Returns a HTMLBuffer with assigned URL handler. """
	buffer = HTMLBuffer(handler = URLHandler.URLHandler)
	return buffer


def get_new_output_window():
	w = OutputWindow()
	return w


def setup_searchBar():
	searchToolbar = SearchBar(None)
	searchToolbar.set_property("name", "searchBar")

	return searchToolbar


def setup_statusIcon():
	"""
	Sets up the status icon.
	"""
	if config.get_bool("tekka", "rgba"):
		gtk.widget_push_colormap(
			widgets.get_widget("mainWindow") \
			.get_screen() \
			.get_rgb_colormap())

	statusIcon = TekkaStatusIcon()
	widgets.add_gobject(statusIcon, "statusIcon")

	if config.get_bool("tekka", "rgba"):
		gtk.widget_pop_colormap()


@types(gladeFile=basestring, section=basestring)
def load_widgets(gladeFile, section):
	""" load the given section from gladeFile
		into widgets and return them.
		This method is ususally called from main.py
		to initialize the GUI
	"""
	global widgets

	def custom_handler(glade, function_name, widget_name, *x):
		if widget_name == "searchBar":
			return setup_searchBar()

		elif widget_name == "outputShell":
			return OutputShell(OutputWindow())

		elif widget_name == "generalOutput":
			t = OutputTextView()
			t.set_buffer(GOHTMLBuffer(handler = URLHandler.URLHandler))
			t.show()

			return t

		elif widget_name == "inputBar":
			try:
				bar = SpellEntry()
			except NameError:
				bar = gtk.Entry()

			bar.show()

			return bar

		elif widget_name == "notificationWidget":
			align = gtk.VBox()
			align.set_no_show_all(True)
			align.set_property("visible", False)

			return align

		return None

	gtk.glade.set_custom_handler(custom_handler)

	gladeObj = gtk.glade.XML(gladeFile, section)

	widgets.set_glade_widgets(gladeObj)

	def setup_mainmenu_context():
		from ..menus.mainmenu_context import MainMenuContext
		return MainMenuContext(name = "mainMenuBar", widgets = widgets)

	mainmenu = setup_mainmenu_context()
	widgets.add_gobject(mainmenu, "mainMenuContext")

	return gladeObj


class GladeWrapper(object):
	""" wrap glade to gtk.Builder """

	def __init__(self, glade):
		self.glade = glade

	def get_object(self, name):
		return self.glade.get_widget(name)

	def connect_signals(self, obj, user = None):
		if type(obj) == dict:
			self.glade.signal_autoconnect(obj)

	def __getattr__(self, attr):
		if attr in ("get_object","connect_signals"):
			return object.__getattr__(self, attr)
		return getattr(self.glade, attr)


def load_menu(name):
	# menus are gtkbuilder
	path = os.path.join(
					config.get("gladefiles", "menus"),
					name + ".ui")

	builder = gtk.Builder()
	builder.add_from_file(path)

	return builder


def load_dialog(name, custom_handler = None):
	path = os.path.join(
					config.get("gladefiles", "dialogs"),
					name + ".glade")

	if custom_handler:
		gtk.glade.set_custom_handler(custom_handler)

	return GladeWrapper(gtk.glade.XML(path))


