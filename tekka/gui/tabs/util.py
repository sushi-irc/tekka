from .._builder import widgets

from ...helper import color

"""
Provides utility functions used by (nearly) all tabs.
"""

def _write_to_general_output(msgtype, timestring, tab, message):
	""" write the given data well-formatted to the general output.
		channel can be empty
	"""
	goBuffer = widgets.get_object("general_output").get_buffer()

	if (tab.is_channel() or tab.is_query()):
		# channel print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s:%s&gt; %s" % (
						   timestring,
						   tab.server.name,
						   tab.name,
						   message),
						tab,
						msgtype)
	else:
		# server print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s&gt; %s" % (
						   timestring,
						   tab.name,
						   message),
						tab,
						msgtype)

	widgets.get_object("general_output").scroll_to_bottom()


def _markup_color(key):
	return color.get_color_by_key(key,
		color.get_widget_base_color(widgets.get_object("tabs_view")))
