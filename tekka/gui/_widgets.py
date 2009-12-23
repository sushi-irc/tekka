import gtk
import gobject

from ..typecheck import types

class WidgetsWrapper(object):

	""" Wrap a glade XML widget object
		so one can manually add own widgets
		and access them as if they lie in
		the XML object.

		Every unknown method call will be
		forwarded to the glade object.
	"""

	def __init__(self, glade_widgets):
		self.glade_widgets = glade_widgets
		self.own_widgets = {}

	def _add_local(self, obj, name):
		""" add an object to the local dict. Checks
			if a object with the same name does already
			exist and raises a ValueError if that's the
			case.
		"""
		if not self.glade_widgets.get_widget(name):
			self.own_widgets[name] = obj

		else:
			raise ValueError, "Widgets '%s' already in widgets dict." % (
				name)

	def set_glade_widgets(self, gladeObject):
		self.glade_widgets = gladeObject

	@types (widget = gobject.GObject)
	def add_gobject(self, obj, name):
		self._add_local(obj, name)

	@types (widget = gtk.Widget)
	def add_widget(self, widget):
		""" Add a widget to the dictionary.

			Throws ValueError if the widget's name
			exists in the glade object.
		"""
		name = widget.get_property("name")

		try:
			self._add_local(widget, name)

		except ValueError:
			raise

		else:
			# XXX: does that make sense?
			widget.connect("destroy", lambda x: self.remove_widget(x))

	@types (widget = (basestring, gtk.Widget))
	def remove_widget(self, widget):
		""" Remove our widget by name or by object """

		def remove_by_name(name):
			if self.own_widgets.has_key(name):
				del self.own_widgets[name]

		if isinstance(widget, basestring):
			remove_by_name(widget)

		else:
			remove_by_name(widget.get_property("name"))

	@types (name = basestring)
	def get_widget(self, name):
		""" Return our own widget if found, else look in glade.
			Returns None if no widget is found.
		"""
		try:
			return self.own_widgets[name]
		except KeyError:
			pass

		w = self.glade_widgets.get_widget(name)

		if w:
			return w

		return None

	def __getattr__(self, attr):
		try:
			return object.__getattr__(self, attr)

		except AttributeError:
			return getattr(self.glade_widgets, attr)


widgets = WidgetsWrapper(None)
