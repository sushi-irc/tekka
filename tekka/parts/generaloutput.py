from .. import gui
from ..lib.general_output_buffer import GOHTMLBuffer
from ..helper.URLHandler import URLHandler


class GeneralOutput(object):

	def __init__(self, tekka):
		self.tekka = tekka
		self.setup()

	def setup(self):
		""" set the textview's buffer to a GOHTMLBuffer and add
			the textview as general_output to the widgets store
		"""
		w = gui.widgets.get_object("general_output_window")
		w.textview.set_buffer(GOHTMLBuffer(handler=URLHandler))
		self.tekka.widgets.add_object(w.textview, "general_output")

		# set general output font
		gui.mgmt.set_font(gui.widgets.get_object("general_output"),
						  gui.mgmt.get_font())

	def test(self):
		return True

	def widget_signals(self):
		return {}


def setup(tekka):
	return GeneralOutput(tekka)


