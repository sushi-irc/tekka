
from .. import gui
from ..lib.welcome_window import WelcomeWindow


class OutputShell(object):

	def __init__(self, tekka):
		self.tekka = tekka

		gui.shortcuts.add_handlers({
			"clear_outputs": output_shortcut_ctrl_l,
			"output_page_up": output_shortcut_Page_Up,
			"output_page_down": output_shortcut_Page_Down,
			"input_search": output_shortcut_ctrl_f,
			"input_search_further": output_shortcut_ctrl_g,
		})

	def test(self):
		return True

	def widget_signals(self):
		return {
			"output_shell_widget_changed": self.outputShell_widget_changed_cb,
		}

	def outputShell_widget_changed_cb(self, shell, old_widget, new_widget):
		""" old_widget: OutputWindow
			new_widget: OutputWindow

			Set the current content of the output_shell in widgets store.
			- output_window <- new_widget
			- output        <- new_widget.textview
		"""
		if (type(old_widget) == WelcomeWindow
		and type(new_widget) != WelcomeWindow):
			gui.mgmt.visibility.show_welcome_screen(False)

		gui.widgets.remove_object("output_window")
		gui.widgets.add_object(new_widget, "output_window")

		gui.widgets.remove_object("output")
		gui.widgets.add_object(new_widget.textview, "output")




def setup(tekka):
	return OutputShell(tekka)




def output_shortcut_ctrl_l(inputBar, shortcut):
	"""
		Ctrl+L was hit, clear the outputs.
	"""
	gui.mgmt.clear_all_outputs()


def output_shortcut_ctrl_f(inputBar, shortcut):
	""" show/hide the search toolbar """
	sb = gui.widgets.get_object("output_searchbar")

	if sb.get_property("visible"):
		sb.hide()
		gui.widgets.get_object("input_entry").grab_focus()
	else:
		sb.show_all()
		sb.grab_focus()


def output_shortcut_ctrl_g(inputBar, shortcut):
	""" search further """

	gui.widgets.get_object("output_searchbar").search_further()



def output_shortcut_Page_Up(inputBar, shortcut):
	"""
		Page_Up was hit, scroll up in output
	"""
	vadj = gui.widgets.get_object("output_window").get_vadjustment()

	if vadj.get_value() == 0.0:
		return # at top already

	n = vadj.get_value()-vadj.page_size
	if n < 0: n = 0
	gobject.idle_add(vadj.set_value,n)


def output_shortcut_Page_Down(inputBar, shortcut):
	""" Page_Down was hit, scroll down in output """

	vadj = gui.widgets.get_object("output_window").get_vadjustment()

	if (vadj.upper - vadj.page_size) == vadj.get_value():
		return # we are already at bottom

	n = vadj.get_value()+vadj.page_size

	if n > (vadj.upper - vadj.page_size):
		n = vadj.upper - vadj.page_size

	gobject.idle_add(vadj.set_value,n)