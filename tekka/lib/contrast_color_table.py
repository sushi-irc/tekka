import gtk
import gobject

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

		self.set_columns(columns)

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

		try:
			bg = color._get_output_bg_color()
		except:
			# in case of glade or test
			bg = gtk.gdk.Color("#fff")

		for code in self.get_color_palette():
			ccolor = contrast.contrast_render_foreground_color(bg, code)

			button = gtk.ColorButton(ccolor)
			button.connect("button-press-event",
				self.button_press_event, code)
			button.connect("key-press-event",
				self.button_key_press_event, code)

			xoptions = yoptions = gtk.FILL

			self.attach(button, x, x+1, y, y+1, xoptions, yoptions)

			x += 1

			if x == columns:
				x = 0
				y += 1


	def change_color(self, color_code):
		self.emit("color-changed", color_code)


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


	def set_columns(self, columns):
		self.fill(columns)
		self._columns = columns


	def set_contrast_color(self, color_code):
		self._contrast_color = color_code
		self.change_color(color_code)


	columns = property(
		lambda s: s._columns,
		set_columns,
		doc="Number of columns per row. Default is 6.")

	gcolumns = gobject.property(
		getter=lambda s: s.columns,
		setter=set_columns,
		default=6,
		type=int)

	contrast_color = property(
		lambda s: s._contrast_color,
		set_contrast_color,
		doc="The selected color. Default is black.")


gobject.signal_new(
	"color-changed",
	ContrastColorTable,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_INT,))
