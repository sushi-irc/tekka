"""
Copyright (c) 2009-2010 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
	notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
	notice, this list of conditions and the following disclaimer in the
	documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import gtk
import gobject

from ..typecheck import types

class InlineDialog(gtk.HBox):

	def __init__(self,
		icon = gtk.STOCK_DIALOG_WARNING,
		buttons = gtk.BUTTONS_CLOSE):

		"""
		 /!\ I'm a warning!  [Close]

		 /!\ I'm a long warning  [Close]
		     which got no place
			 for buttons.

	     (?) Do you want?   [Yes] [No]
		"""
		def style_set_cb (widget, style, dialog):
			if dialog.setting_style:
				return

			tt = gtk.Window()
			tt.set_name("gtk-tooltip")
			tt.ensure_style()

			# set_style() may cause style-set to be triggered again.
			# It should not happen in our case, but better be safe
			# than sorry.
			dialog.setting_style = True
			dialog.hbox.set_style(tt.get_style().copy())
			dialog.setting_style = False

			tt.destroy()

			dialog.hbox.queue_draw()

		def expose_event_cb (widget, event):
			a = widget.get_allocation()

			widget.style.paint_flat_box(
				widget.window,
				gtk.STATE_NORMAL,
				gtk.SHADOW_ETCHED_IN,
				None,
				widget,
				"tooltip",
				a.x + 1,
				a.y + 1,
				a.width - 2,
				a.height - 2
			)

			return False

		def size_allocate_cb (widget, allocation):
			widget.queue_draw()
			widget.parent.queue_draw()

		gtk.HBox.__init__(self)

		self.set_property("border-width", 6)

		self.setting_style = False

		self.hbox = gtk.HBox(spacing=6)
		self.hbox.set_app_paintable(True)
		self.hbox.set_property("border-width", 6)

		# add icon
		self.icon = gtk.image_new_from_stock(icon, gtk.ICON_SIZE_DIALOG)
		self.icon.set_property("yalign", 0.0)
		self.hbox.add_with_properties(self.icon, "expand", False)

		# add vbox
		self.vbox = gtk.VBox(spacing=6)
		self.hbox.add_with_properties(self.vbox, "padding", 6)

		# add buttonbox
		self.buttonbox = gtk.VButtonBox()
		self.buttonbox.set_layout(gtk.BUTTONBOX_START)
		self.hbox.add_with_properties(self.buttonbox, "expand", False)

		if type(buttons) == gtk.ButtonsType:
			self.apply_buttons_type(buttons)
		else:
			self.add_buttons(*buttons)

		self.connect("style-set", style_set_cb, self)
		self.hbox.connect("expose-event", expose_event_cb)
		self.hbox.connect("size-allocate", size_allocate_cb)

		self.add(self.hbox)

	@types(btype = gtk.ButtonsType)
	def apply_buttons_type(self, btype):
		if btype == gtk.BUTTONS_NONE:
			pass

		elif btype == gtk.BUTTONS_OK:
			self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK)

		elif btype == gtk.BUTTONS_CLOSE:
			self.add_buttons(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

		elif btype == gtk.BUTTONS_YES_NO:
			self.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO)

		elif btype == gtk.BUTTONS_OK_CANCEL:
			self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

	def add_buttons(self, *args):
		""" add_buttons(Label0, ResponseID0, StockID1, ResponseID1, ...) """

		if len(args) % 2 != 0:
			raise ValueError, "Not enough arguments supplied, (Button, Response,...)"

		i = 0
		while i < len(args)-1:

			try:
				stock_info = gtk.stock_lookup(args[i])
			except TypeError:
				stock_info = None

			if stock_info != None:
				# Stock item
				button = gtk.Button(stock = args[i])

			else:
				# Label
				button = gtk.Button(label = args[i])

			button.connect("clicked", lambda w,id: self.response(id), args[i+1])
			self.buttonbox.add(button)

			i += 2

	def response(self, id):
		""" button was activated, react on id """
		self.emit("response", id)

gobject.signal_new("response", InlineDialog, gobject.SIGNAL_ACTION, None, (gobject.TYPE_INT,))

class InlineMessageDialog(InlineDialog):

	def __init__(self, primary, secondary = None, *args, **kwargs):
		InlineDialog.__init__(self, *args, **kwargs)

		# add label
		self.primary_label = gtk.Label()
		self.primary_label.set_markup("<b>%s</b>" % (primary))
		self.primary_label.set_selectable(True)
		self.primary_label.set_property("xalign", 0.0)
		self.primary_label.set_property("yalign", 0.0)
		self.vbox.add(self.primary_label)

		if secondary:
			self.secondary_label = gtk.Label()
			self.secondary_label.set_markup("<small>%s</small>" % (secondary))
			self.secondary_label.set_selectable(True)
			self.secondary_label.set_property("xalign", 0.0)
			self.secondary_label.set_property("yalign", 0.0)
			self.vbox.add(self.secondary_label)

