import gtk

class TekkaBuilder(gtk.Builder):
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
		if self._widgets.has_key(name):
			raise ValueError, "Object '%s' already in Builder." % (name)
		self._widgets[name] = object
		return True

	def remove_object(self, name):
		if self._widgets.has_key(name):
			del self._widgets[name]
			return True
		return False

widgets = TekkaBuilder()
