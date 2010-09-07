import gtk
from gettext import gettext as _

from . import contrast

from ..helper import color

class ContrastColorTable(gtk.Table):

	""" Display all available contrast colors as color buttons
		in n >= 1 rows depending on the column count.
		The default column count is 6.
	"""

	__gtype_name__ = "ContrastColorTable"



	def __init__(self, columns=6):
		super(ContrastColorTable, self).__init__()

		self.fill(columns)

		self.contrast_color = contrast.CONTRAST_COLOR_BLACK


	def get_color_palette(self):
		return [
			contrast.CONTRAST_COLOR_BLACK,
			contrast.CONTRAST_COLOR_WHITE,
			contrast.CONTRAST_COLOR_LIGHT_GREY,
			contrast.CONTRAST_COLOR_GREY,
			contrast.CONTRAST_COLOR_LIGHT_GREEN,
			contrast.CONTRAST_COLOR_AQUA,
			contrast.CONTRAST_COLOR_DARK_GREEN,
			contrast.CONTRAST_COLOR_CYAN,
			contrast.CONTRAST_COLOR_LIGHT_BLUE,
			contrast.CONTRAST_COLOR_BLUE,
			contrast.CONTRAST_COLOR_PURPLE,
			contrast.CONTRAST_COLOR_MAGENTA,
			contrast.CONTRAST_COLOR_LIGHT_BROWN,
			contrast.CONTRAST_COLOR_DARK_RED,
			contrast.CONTRAST_COLOR_ORANGE,
			contrast.CONTRAST_COLOR_YELLOW,
		]


	def fill(self, columns):
		""" fill the table """
		self.foreach(lambda w: self.remove(w))

		x,y = (0,0)
		bg = color._get_output_bg_color()

		for code in self.get_color_palette():
			ccolor = contrast.contrast_render_foreground_color(bg, code)

			button = gtk.ColorButton(ccolor)
			button.connect("button-press-event",
				self.button_press_event, code)
			button.connect("key-press-event",
				self.button_key_press_event, code)

			self.attach(button, x, x+1, y, y+1)

			x += 1

			if x == columns:
				x = 0
				y += 1

		self._attach_textview(y+1, columns)


	def _attach_textview(self, row, columns):
		self.textview = gtk.TextView()

		self.color_tag = self.textview.get_buffer().create_tag()

		self.textview.get_buffer().insert_with_tags(
			self.textview.get_buffer().get_end_iter(),
			_("The quick brown fox jumps over the lazy developer."),
			self.color_tag)
		self.attach(self.textview, 0, columns, row, row+1)


	def change_color(self, color_code):
		self.color_tag.set_property("foreground",
			contrast.contrast_render_foreground_color(
				color._get_output_bg_color(), color_code))


	def button_press_event(self, button, event, color_code):
		if event.type == gtk.gdk.BUTTON_PRESS:
			self.contrast_color = color_code
			return True
		return False


	def button_key_press_event(self, button, event, color_code):
		if (event.type == gtk.gdk.KEY_PRESS and
		gtk.gdk.keyval_name(event.keyval) in ("Return","space")):
			self.contrast_color = color_code
			return True
		return False


	def set_contrast_color(self, color_code):
		self._contrast_color = color_code
		self.change_color(color_code)


	contrast_color = property(
		lambda s: s._contrast_color,
		set_contrast_color,
		doc="The selected color. Default is black.")
