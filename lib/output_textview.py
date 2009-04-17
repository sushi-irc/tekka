
import gtk
from lib.htmlbuffer import HTMLBuffer
from helper import URLHandler

class OutputTextView(gtk.TextView):

	def __init__(self):
		gtk.TextView.__init__(self,
			HTMLBuffer(handler = URLHandler.URLHandler))

		self.set_property("editable", False)
		self.set_property("can-focus", False)
		self.set_property("wrap-mode", gtk.WRAP_WORD_CHAR)
		self.set_property("cursor-visible", False)

	def scroll_to_bottom(self):
		tb = self.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		self.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)


