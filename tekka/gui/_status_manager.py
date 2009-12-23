import gobject

class StatusManager(gobject.GObject):

	""" Hold the different states the application is in.
		Every state has an ID which can be retrieved by
		id(status). A status can be set or be unset or
		retrieved by get(status)
	"""

	def __init__(self):
		gobject.GObject.__init__(self)
		self.states = []

	def set(self, status):
		""" Set the given status """
		try:
			self.states.index(status)
		except ValueError:
			self.states.append(status)
			self.emit("set-status", status)
			return True
		return False

	def set_visible(self, status, message):
		""" Set the given status with a message which can be processed """
		if self.set(status):
			self.emit("set-visible-status", status, message)

	def unset(self, status):
		""" Unset the given status """
		try:
			index = self.states.index(status)
		except ValueError:
			return False
		self.emit("unset-status", status)
		del self.states[index]
		return True

	def get(self, status):
		""" return True if status is set, otherwise False """
		try:
			self.states.index(status)
		except ValueError:
			return False
		else:
			return True

	def id(self, status):
		""" return an unique ID for the given status if it's set.
			Otherwise raise a ValueError
		"""
		try:
			return self.states.index(status)
		except ValueError:
			raise ValueError, "Status %s not in state list." % (status)

gobject.signal_new("set-status", StatusManager, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_STRING,))
gobject.signal_new("set-visible-status", StatusManager,
	gobject.SIGNAL_ACTION, None, (gobject.TYPE_STRING, gobject.TYPE_STRING))
gobject.signal_new("unset-status", StatusManager, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_STRING,))

status = StatusManager()
