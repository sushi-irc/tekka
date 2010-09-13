
import gtk
import gobject

from .. import gui
from ..lib import contrast
from ..helper import color as hcolor
from ..typecheck import types

class ColorDialog(object):

	""" show the available contrast colors as colored buttons
		and show a textfield with text foreground colored in
		the selected color.
	"""

	def __init__(self):
		self.builder = gui.builder.load_dialog("contrast")

		self._setup_text_tag()

		self.builder.connect_signals(self)

		self._colors = (None,None)


	def __getattr__(self, attr):
		if attr in ("builder", "color_tag", "_colors"
					"_setup_text_tag", "set_example_color",
					"get_current_color", "show_all",
					"set_current_rgb_color",
					"set_current_contrast_color",
					"contrast_color_table_color_changed",
					"colorselection_color_changed"):
			# public attributes of this object
			return super(ColorDialog,self).__getattr__(attr)
		else:
			return getattr(self.builder.get_object("contrast_dialog"), attr)


	def show_all(self):
		# FIXME:  for a reason i don't know yet, show_all() does not
		# FIXME:: apply show for the contrast_color_table, so this fixes it
		self.builder.get_object("contrast_dialog").show_all()
		self.builder.get_object("contrast_color_table").show_all()


	def _setup_text_tag(self):
		buffer = self.builder.get_object("example_text_view").get_buffer()

		self.color_tag = buffer.create_tag()

		buffer.apply_tag(self.color_tag, buffer.get_start_iter(),
			buffer.get_end_iter())


	def set_example_color(self, color):
		self.color_tag.set_property("foreground", color)


	def set_current_rgb_color(self, color):
		self.builder.get_object("colorselection").set_current_color(color)


	@types(color_code=int)
	def set_current_contrast_color(self, color_code):
		""" take a contrast color number and behave as if the specific
			color is selected.
		"""
		table = self.builder.get_object("contrast_color_table")

		button = table.get_button_by_code(color_code)
		button.clicked()


	def get_current_color(self):
		""" return a tuple with two values like this:
				(<gtk.gdk.Color()>,<contrast color code>).

			If a color is set by the colorselection, no contrast color
			is set:
				(<gtk.gdk.Color(...)>, None).

			If a contrast color is used, the first value is the RGB
			representation of the contrast color and the second value
			is the contrast color code:
				(<gtk.gdk.Color(...), <contrast color code>).

			Default is (None, None).
		"""
		return self._colors


	def contrast_color_table_color_changed(self, table, color_code):
		color = contrast.contrast_render_foreground_color(
					hcolor._get_output_bg_color(), color_code)

		# set the colorselection to the contrast color
		self.builder.get_object("colorselection").set_current_color(color)

		self._colors = (color, color_code)

		self.set_example_color(color)


	def colorselection_color_changed(self, selection):
		color = selection.get_current_color()

		self._colors = (color, None)

		self.set_example_color(color)



def setup():pass

def run(parent=None):
	d = ColorDialog()

	if parent:
		d.set_transient_for(parent)

	d.show_all()
	return d
