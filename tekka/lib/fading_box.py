"""
Copyright (c) 2010 Marian Tietz
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

import gobject
import gtk

from threading import Timer


class FadingBox(gtk.EventBox):

	""" Has the ability to fade it's background color to another """

	""" NOTE: color attributes suffer from integer overflow (0xffff) """

	MAX_FADING_TIME = 700 # miliseconds

	origin_bg_color = property(lambda s: s._origin_bg_color.copy(), None)

	def __init__(self):
		super(FadingBox,self).__init__()

		self._origin_bg_color = self.get_style().bg[gtk.STATE_NORMAL].copy()
		self._timeout_id = None
		self._timer = None


	def reset_background(self):
		""" reset the background color to what it should be according
			to the gtkrc loaded
		"""

		style = self.get_style().copy()
		style.bg[gtk.STATE_NORMAL] = self._origin_bg_color.copy()
		self.set_style(style)


	def _fade_timeout(self, color):

		def do_timeout(self, color):
			style = self.get_style().copy()
			style.bg[gtk.STATE_NORMAL] = color.copy()
			self.set_style(style)

			self.stop_fading()
		gobject.idle_add(do_timeout, self, color)
		return False


	def _fade_channel(self, channel, reference):

		if channel == reference:
			return (True, reference)

		if channel > reference:
			up = (channel / 10) + 1
			if channel-up < 0 or channel-up < reference:
				return (True, reference)
			return (False, channel-up)

		else:
			up = (reference / 10) + 1
			if channel+up >= 0xffff or channel+up > reference:
				return (True, reference)
			return (False, channel+up)


	def _fade_bg(self, color):
		""" modifiy each color channel of the background color according
			to color and refresh the style with the new background color
		"""

		if not self._timeout_id:
			return False

		bg_color = self.bg_color

		(rdone, bg_color.red) = self._fade_channel(bg_color.red,
												   color.red)
		(gdone, bg_color.green) = self._fade_channel(bg_color.green,
													 color.green)
		(bdone, bg_color.blue) = self._fade_channel(bg_color.blue,
													color.blue)


		self.bg_color = bg_color

		style = self.get_style().copy()
		style.bg[gtk.STATE_NORMAL] = bg_color.copy()
		self.set_style(style)

		if rdone and gdone and bdone:
			self.stop_fading()
			return False

		return True


	def fade(self, to_color, interval=40):
		""" fade the background color of this box to the given color.
			interval is the time in miliseconds between each fade
		"""

		if self._timeout_id:
			return False # already fading


		style = self.get_style()
		self.bg_color = style.bg[gtk.STATE_NORMAL].copy()

		self._timeout_id = gobject.timeout_add(interval,
											   self._fade_bg,
											   to_color)

		self._timer = gobject.timeout_add(self.MAX_FADING_TIME,
										  self._fade_timeout,
										  to_color)

		return True

	def stop_fading(self):

		if self._timeout_id:
			gobject.source_remove(self._timeout_id)
			gobject.source_remove(self._timer)

			self._timeout_id = None
			self._timer = None

			self.emit("fade-finished")


gobject.signal_new("fade-finished", FadingBox, gobject.SIGNAL_ACTION,
				   None, ())


if __name__ == "__main__":

	win = gtk.Window()
	win.set_default_size(500,300)

	vbox = gtk.VBox()
	win.add(vbox)

	box = FadingBox()
	vbox.pack_start(box)

	btn = gtk.Button("Green")
	vbox.add(btn)

	btn2 = gtk.Button("Background")
	vbox.add(btn2)

	btn3 = gtk.Button("Blue")
	vbox.add(btn3)

	btn4 = gtk.Button("Red")
	vbox.add(btn4)

	box.fade(gtk.gdk.Color("#0000ff"))

	btn5 = gtk.Button("Black")
	vbox.add(btn5)

	def btn_clicked_cb(btn):
		"""
		def do_setup():

			def new_fade(box):
				if new_fade.ran:
					return

				print "new fade"
				c = gtk.gdk.Color("#FF0000")
				box.fade(c)
				new_fade.ran = True

			c = gtk.gdk.Color("#00FF00")
			box.fade(c)
			new_fade.ran = False

			if not btn_clicked_cb.init:
				box.connect("fade-finished", new_fade)
				btn_clicked_cb.init = True


		box.stop_fading()
		box.reset_background()

		gobject.timeout_add(1000, do_setup)
		"""

		"""
		def finished_cb(box, callback):
			self = finished_cb

			if self.count == 0:
				callback()
				return

			if self.back_fade:
				gobject.idle_add(box.fade, self.two)
			else:
				gobject.idle_add(box.fade, self.one)

			self.back_fade = not self.back_fade
			self.count -= 1

		def killsig():
			box.disconnect(killsig.handle)

		handle = box.connect("fade-finished", finished_cb, killsig)
		finished_cb.back_fade = False
		finished_cb.one = gtk.gdk.Color("#0f0")
		finished_cb.two = box.origin_bg_color
		finished_cb.count = 4

		killsig.handle = handle

		box.fade(gtk.gdk.Color("#0f0"))
		"""

		box.fade(gtk.gdk.Color("#0f0"))


	def btn2_clicked_cb(btn):

		box.fade(box.origin_bg_color)


	def btn3_clicked_cb(btn):

		box.fade(gtk.gdk.Color("#00f"))


	def btn4_clicked_cb(btn):

		box.fade(gtk.gdk.Color("#f00"))


	def btn5_clicked_cb(btn):

		box.fade(gtk.gdk.Color("#000"))


	btn_clicked_cb.init = False
	btn.connect("clicked", btn_clicked_cb)
	btn2.connect("clicked", btn2_clicked_cb)
	btn3.connect("clicked", btn3_clicked_cb)
	btn4.connect("clicked", btn4_clicked_cb)
	btn5.connect("clicked", btn5_clicked_cb)

	win.connect("destroy", lambda w: gtk.main_quit())
	win.show_all()

	gtk.main()
