import gtk
import gobject

from .output_textview import OutputTextView

from math import ceil

class OutputWindow(gtk.ScrolledWindow):

	""" A gtk.ScrolledWindow with a TextView inside of it.

		This widget watches for autoscrolling and
		adjusts the scrollbar on size-allocations.

		This widget is supposed to be hold by a OutputShell.
	"""

	def __init__(self):
		gtk.ScrolledWindow.__init__(self)

		self.set_properties(
			hscrollbar_policy = gtk.POLICY_NEVER,
			vscrollbar_policy = gtk.POLICY_AUTOMATIC,
				  shadow_type = gtk.SHADOW_ETCHED_IN )

		self.textview = OutputTextView()
		self.auto_scroll = True

		self.add(self.textview)

		self.old_allocation = self.get_allocation()

		# XXX: redundant code, see main.py::setup_mainWindow
		def kill_mod1_scroll_cb(w,e):
			if e.state & gtk.gdk.MOD1_MASK:
				w.emit_stop_by_name("scroll-event")

		self.connect("scroll-event", kill_mod1_scroll_cb)

		def size_allocate_cb(win, alloc):
			""" Called when the window has a new size.
				If the new size differs from the old size,
				determine if we wanted to be at the bottom
				(auto_scroll = True) and scroll down.
			"""
			adj = win.get_vscrollbar().get_adjustment()

			if alloc.height != self.old_allocation.height:

				if self.auto_scroll:

					def doit():
						self.textview.scroll_to_bottom(no_smooth = True)
						return False

					gobject.idle_add(doit)

			self.old_allocation = alloc

		self.connect("size-allocate", size_allocate_cb)

		def value_changed_cb(sbar):
			""" Called if the scrollbar value has changed.

				If the scrollbar is at the bottom,
				set auto_scroll to True.

				If we're in the middle of a smooth scrolling
				action, and self.auto_scroll is True, it will
				be True after all.

				In all other cases, we don't want auto scroll
				anymore.
			"""

			def idle_handler_cb():
				adjust = sbar.get_property("adjustment")

				if (self.auto_scroll
				and self.textview.is_smooth_scrolling()):

					# XXX: instead of setting, ignore this completely.
					self.auto_scroll = True

				elif ceil(adjust.upper - adjust.page_size) \
				 == ceil(sbar.get_value()):

					self.auto_scroll = True

				else:
					self.auto_scroll = False

				return False

			# XXX:  maybe one can get rid of this if using connect_after
			# XXX:: instead of connect
			gobject.idle_add(idle_handler_cb)

		self.get_vscrollbar().connect("value-changed", value_changed_cb)

