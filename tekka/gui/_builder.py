import gtk

"""

Holds the TekkaBuilder class object, initially needed for
the builder module.

Also provides a static reference to the initial instance of
the TekkaBuilder class (widgets) which is used all over
the application to access widgets.

"""

class TekkaBuilder(gtk.Builder):
	""" extended version of the gtk.Builder which supports
		adding GObject widgets to the list of storable
		objects in the builder.
	"""

	def __init__(self):
		super(TekkaBuilder,self).__init__()
		self._widgets = {}

	def get_object(self, name):
		obj = super(TekkaBuilder,self).get_object(name)
		if obj:
			return obj
		if self._widgets.has_key(name):
			return self._widgets[name]
		return None

	def add_object(self, object, name):
		if (super(TekkaBuilder,self).get_object(name)
		or self._widgets.has_key(name)):
			raise ValueError, "Object '%s' already in Builder." % (name)
		self._widgets[name] = object
		return True

	def remove_object(self, name):
		if self._widgets.has_key(name):
			del self._widgets[name]
			return True
		return False


widgets = TekkaBuilder()
