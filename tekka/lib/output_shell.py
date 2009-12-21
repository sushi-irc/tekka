import gtk
import gobject

from .output_window import OutputWindow
from ..typecheck import types

class OutputShell(gtk.VBox):

	""" A shell for one OutputWindow with
		methods to display another OutputWindow.
	"""

	@types (widget = OutputWindow)
	def __init__(self, window):
		""" Takes a default window which is shown if reset() is
			called (which is the default).
		"""
		gtk.VBox.__init__(self)

		self.init_window = window
		self.output_window = None

		self.reset()

	@types (new_window = OutputWindow)
	def set(self, new_window):
		""" Set a new OutputWindow which replaces
			the current.

			Emits widget-changed with the old and the
			new widget.
		"""
		old_window = self.output_window

		if old_window:
			self.remove(old_window)

		self.pack_start(new_window)
		self.output_window = new_window

		self.emit("widget-changed", old_window, new_window)

	def reset(self):
		""" Reset to the default window. """
		self.set(self.init_window)

	def get(self):
		""" Return the current OutputWindow """
		return self.output_window

gobject.signal_new(
	"widget-changed", OutputShell,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))

