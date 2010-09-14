from ..builder import widgets, build_status_icon
from ... import config
from ...lib.welcome_window import WelcomeWindow


def _show_hide(widget, show, all=False):
	if show:
		if all: widget.show_all()
		else: widget.show()
	else:
		if all: widget.hide_all()
		else: widget.hide()

def show_topic_bar(show):
	_show_hide(widgets.get_object("topic_alignment"), show, all=True)

def show_status_icon(show):
	icon = widgets.get_object("status_icon")

	if show:
		if not icon:
			build_status_icon()
			return
	else:
		if not icon:
			return
	icon.set_visible(show)

def show_status_bar(show):
	_show_hide(widgets.get_object("statusbar"), show)

def show_side_pane(show):
	_show_hide(widgets.get_object("list_vpaned"), show)

def show_general_output(show):
	_show_hide(widgets.get_object("general_output_alignment"), show,
		all=True)

def show_nicks(show):
	_show_hide(widgets.get_object("nicks_vbox"), show)

def show_welcome_screen(show):
	""" show a welcome screen while hiding general output,
		topic bar and side pane.
	"""

	# widgets to hide on welcome
	hides = (
		"show_side_pane",
		"show_topic_bar",
		"show_general_output"
	)

	for to_hide in hides:
		if config.get_bool("tekka",to_hide):
			# it should be showed, hide it if welcome
			# screen should be showed, otherwise show it
			eval(to_hide)(not show)

	if show:
		s = widgets.get_object("output_shell")

		w = WelcomeWindow()

		s.set(w)
		s.show_all()



def apply_visibility_from_config():
	""" read the config values of the widgets which can be
		hidden and apply the configured value to the widgets
	"""

	c_w = {
		"show_general_output": show_general_output,
		"show_topic_bar": show_topic_bar,
		"show_side_pane": show_side_pane,
		"show_status_bar": show_status_bar,
		"show_status_icon": show_status_icon,
		}

	for option in c_w:
		c_w[option](config.get_bool("tekka", option))



