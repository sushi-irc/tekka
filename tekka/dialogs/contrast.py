
import gtk
import gobject

from .. import gui
from ..lib import contrast

class ColorDialog(gobject.GObject):

	""" show the available contrast colors as colored buttons
		and show a textfield with text foreground colored in
		the selected color.
	"""

	def __init__(self):
		self.builder = gui.builder.load_dialog("colorDialog")

		self._setup_text_tag()

		builder.connect_signals(self)


	def _setup_text_tag(self):
		buffer = self.builder.get_object("example_text_view").get_buffer()

		self.color_tag = buffer.create_tag()
		buffer.apply_tag(self.color_tag, 0, buffer.get_char_count())


	def contrast_color_table_color_changed(self, table, color_code):
		self.color_tag.set_property("foreground",
			contrast.contrast_render_foreground_color(
				color._get_output_bg_color(), color_code))


def setup():pass

def run(*_):
	d = ColorDialog()
	d.show_all()
	return d
