from ..builder import widgets, build_status_icon

def _show_hide(widget, show):
	if show: widget.show()
	else: widget.hide()

def show_topic_bar(show):
	_show_hide(widgets.get_object("topic_alignment"), show)

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
	_show_hide(widgets.get_object("general_output_alignment"), show)

