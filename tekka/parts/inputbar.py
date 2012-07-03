import gtk

from .. import gui

from ..helper import tabcompletion


class InputBar(object):

	def __init__(self, tekka):
		self.tekka = tekka

		# set input font
		gui.mgmt.set_font(gui.widgets.get_object("input_entry"),
						  gui.mgmt.get_font())

		gui.shortcuts.add_handlers({
			"input_clear_line": inputBar_shortcut_ctrl_u,
			"input_copy": inputBar_shortcut_ctrl_c,
		})

	def test(self):
		return True


	def widget_signals(self):
		return 	{
			# Input entry...
			"input_entry_activate":
				inputBar_activate_cb,
			"input_entry_key_press_event":
				inputBar_key_press_event_cb,
		}


def setup(tekka):
	return InputBar(tekka)



def inputBar_activate_cb(inputBar):
	""" Enter hit, pass the inputBar text over to the
		commands.parseInput method and add the text to the input history.

		The inputBar is cleared after that.
	"""

	text = inputBar.get_text()

	tab = gui.tabs.get_current_tab()

	commands.parseInput(text)

	if tab:
		tab.input_history.add_entry(text)
		tab.input_history.reset()

	inputBar.set_text("")


def inputBar_key_press_event_cb(inputBar, event):
	""" Up -> Input history previous entry
		Down -> Input history next entry
		Tab -> Completion of the current word

		Everything else than tab ->
			No further completion wished, tell that.
	"""

	key =  gtk.gdk.keyval_name(event.keyval)
	tab =  gui.tabs.get_current_tab()

	text = unicode(inputBar.get_text(), "UTF-8")

	if key == "Up":
		# get next input history item
		if not tab:
			return

		hist = tab.input_history.get_previous()

		if hist != None:
			inputBar.set_text(hist)
			inputBar.set_position(len(hist))

	elif key == "Down":
		# get previous input history item
		if not tab:
			return

		hist = tab.input_history.get_next()

		if hist == None:
			return

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))

	elif key == "Tab":
		# tab completion comes here.

		tabcompletion.complete(tab, inputBar, text)
		return True

	if key != "Tab":
		tabcompletion.stopIteration()



def inputBar_shortcut_ctrl_u(inputBar, shortcut):
	""" Ctrl + U was hit, clear the inputBar """

	gui.widgets.get_object("input_entry").set_text("")


def inputBar_shortcut_ctrl_c(inputBar, shortcut):
	"""
		Ctrl + C was hit.
		Check every text input widget for selection
		and copy the selection to clipboard.
		FIXME: this solution sucks ass.
	"""
	buffer = gui.widgets.get_object("output").get_buffer()
	goBuffer = gui.widgets.get_object("general_output").get_buffer()
	topicBar = gui.widgets.get_object("topic_label")
	cb = gtk.Clipboard()

	if buffer.get_property("has-selection"):
		buffer.copy_clipboard(cb)
	elif inputBar.get_selection_bounds():
		inputBar.copy_clipboard()
	elif goBuffer.get_property("has-selection"):
		goBuffer.copy_clipboard(cb)
	elif topicBar.get_selection_bounds():
		bounds = topicBar.get_selection_bounds()
		text = unicode(topicBar.get_text(), "UTF-8")
		text = text[bounds[0]:bounds[1]]
		cb.set_text(text)

