import gtk

class CustomColorButton(gtk.ColorButton):

	""" A ColorButton which leaves it to the developer what
		to open after a click.
	"""

	__gtype_name__ = "CustomColorButton"

	def do_clicked(self):
		pass

	def do_color_set(self):
		pass

