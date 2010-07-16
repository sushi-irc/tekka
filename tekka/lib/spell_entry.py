import gtk
import pango

from gettext import gettext as _

from ..helper import color
from ..lib import contrast


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

		self.connect("activate", lambda s,*u: s._apply_color_tags())


	def _determine_popup_menu(self,  widget,  menu,  *user):
		self._popup_menu_handler(menu)


	# TODO:
	# nothing marked: set color for whole text:  { "all" : {"fg":x,"bg":y} }
	# text marked: set color for specific text: { ..., (n,m) : {"fg":x,"bg":y} }
	# nothing marked & dict !empty: goto "nothing marked"
	# text marked & dict !empty: goto "text marked"

	# TODO: mark color setting visually via the pango Layout (set_markup)

	# TODO: determine what happens if the user edits the text...

	def _apply_color_tags(self):
		pass
	
	def _new_range_entry(self, id, before=False):
		self._ranges[id] = {"fg":None,"bg":None}
		
	def _new_attr(self, atype, colorcode, start, end):
		
		def get_gdk_color(ccolor):
			bg_color = self.get_style().base[gtk.STATE_NORMAL]
			return contrast.contrast_render_foreground_color(
					bg_color, ccolor)
		
		gcolor = get_gdk_color(colorcode)
		if atype == "fg":
			return pango.AttrForeground(gcolor.red, gcolor.green, gcolor.blue,
										start, end)
		elif atype == "bg":
			return pango.AttrBackground(gcolor.red, gcolor.green, gcolor.blue,
										start, end)
	
	def _dump_attributes(self):
		a = self.get_layout().get_attributes()
		i = a.get_iterator()
		o = []
		while True:
			l = i.get_attrs()
			o.append(l)
			if not i.next():
				break
		print o
	
	def _modify_general_color(self, fg="", bg=""):
		if not self._ranges.has_key("all"):
			self._new_range_entry("all")	
			
		elem = self._ranges["all"]
			
		if fg:
			fg_attr = self._new_attr("fg", fg, 0, self.get_text_length())
			elem["fg"] = fg_attr
			self.get_layout().get_attributes().change(fg_attr)
			self._dump_attributes()
			self.get_layout().context_changed()
		if bg:
			bg_attr = self._new_attr("bg", bg, 0, self.get_text_length())
			elem["bg"] = bg_attr
			self.get_layout().get_attributes().insert(bg_attr)
			self._dump_attributes()
			self.get_layout().context_changed()


		
	def _add_range_color(self, start, end, fg="",bg=""):
		if not bg and not fg: return
		if not self._ranges.has_key((start,end)):
			self._new_range_entry((start,end))
			
		elem = self._ranges[(start,end)]
		
		if fg:
			fg_attr = self._new_attr("fg", fg, start, end)
			elem["fg"] = fg_attr
			self.get_layout().get_attributes().insert(fg_attr)
			self._dump_attributes()
		if bg:
			bg_attr = self._new_attr("bg", bg ,start, end)
			elem["bg"] = bg_attr
			self.get_layout().get_attributes().insert(bg_attr)
			self._dump_attributes()

	def _fg_item_activate(self, item, value):
		bounds = self.get_selection_bounds()
		if not bounds:
			self._modify_general_color(fg=value)
		else:
			self._add_range_color(*bounds, fg=value)

	def _bg_item_activate(self, item, value):
		bounds = self.get_selection_bounds()
		if not bounds:
			self._modify_general_color(bg=value)
		else:
			self._add_range_color(*bounds, bg=value)

	def _reset_item_activate(self, item):
		bounds = self.get_selection_bounds()
		if not bounds:
			self._ranges = {}
		elif self._ranges.has_key((bounds[0],bounds[1])):
			del self._ranges[(bounds[0],bounds[1])]
		elif bounds:
			for (cbounds,colors) in self._ranges.items():
				if cbounds == "all": continue
				start,end = cbounds
				wstart,wend = bounds
				if wstart >= start and wend <= end:
					del self._ranges[cbounds]
					return
			
		# if we reach this, we have not found a suitable entry, maybe
		# the user means to reset it all but has a selection. reset all.
		self._ranges = {}

	def _popup_menu_handler(self,  menu):
		
		# FIXME: remove this if everything works..
		return

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
        
		reset_item = gtk.MenuItem(label=_("Reset Color"))
		reset_item.connect("activate", self._reset_item_activate)
		reset_item.show()
		menu.insert(reset_item, 2)
