import gtk
from ..helper import color
from gettext import gettext as _

try:
	from sexy import SpellEntry as _SpellEntry
except ImportError:
	from gtk import Entry as _SpellEntry

class SpellEntry(_SpellEntry):

	__gtype_name__ = "SpellEntry"

	def __init__(self, *args,  **kwargs):
		super(SpellEntry, self).__init__(*args, **kwargs)

		self._ranges = {}

		self.connect("populate-popup",  self._determine_popup_menu)

		self.connect("activate",  lambda s, x, *u: s._apply_color_tags())


	def _determine_popup_menu(self,  widget,  menu,  *user):
		self._popup_menu_handler(menu)


	# TODO:
	# nothing marked: set color for whole text:  { (0,n) : {"fg":x,"bg":y} }
	# text marked: set color for specific text: { ..., (n,m) : {"fg":x,"bg":y} }
	# nothing marked & dict !empty: clear dict & goto "nothing marked"
	# text marked & dict !empty: goto "text marked"

	# TODO: mark color setting visually via the pango Layout (set_markup)

	# TODO: determine what happens if the user edits the text...

	def _apply_color_tags(self):
		pass

	def _fg_item_activate(self,  value):
		pass

	def _bg_item_activate(self,  value):
		pass

	def _popup_menu_handler(self,  menu):

		fg_item = gtk.MenuItem(label=_("Foreground Color"))
		fg_submenu = gtk.Menu()

		for (value, name) in color.COLOR_NAMES.items():
			item = gtk.MenuItem(label=" ".join([n.capitalize() for n in name.split(" ")]))
			item.connect("activate", self._fg_item_activate,  value)
			fg_submenu.append(item)

		fg_item.set_submenu(fg_submenu)
		fg_item.show_all()
		menu.insert(fg_item,  0)

		bg_item = gtk.MenuItem(label=_("Background Color"))
		bg_submenu = gtk.Menu()

		for (value, name) in color.COLOR_NAMES.items():
			item = gtk.MenuItem(label=" ".join([n.capitalize() for n in name.split(" ")]))
			item.connect("activate", self._bg_item_activate,  value)
			bg_submenu.append(item)

		bg_item.set_submenu(bg_submenu)
		bg_item.show_all()
		menu.insert(bg_item,  1)
