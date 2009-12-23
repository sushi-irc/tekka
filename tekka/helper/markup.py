import gobject

from . import escape as escape_helper
from . import color

def _escape_ml(msg):
	""" escape every invalid character via gobject.markup_escape_text
		from the given string but leave the irc color/bold characters:
		- chr(2)
		- chr(3)
		- chr(31)
	"""

	msg = msg.replace("%","%%") # escape %
	msg = msg.replace(chr(2), "%2")
	msg = msg.replace(chr(31), "%31")
	msg = msg.replace(chr(3), "%3")

	msg = gobject.markup_escape_text(msg)

	l = escape_helper.unescape_split("%2", msg, escape_char="%")
	msg = chr(2).join(l)

	l = escape_helper.unescape_split("%3", msg, escape_char="%")
	msg = chr(3).join(l)

	l = escape_helper.unescape_split("%31", msg, escape_char="%")
	msg = chr(31).join(l)

	return msg.replace("%%","%")


def markup_escape(msg):
	""" escape for pango markup language """
	msg = _escape_ml(msg)

	# don't want bold/underline, can't use it
	msg = msg.replace(chr(2), "")
	msg = msg.replace(chr(31), "")

	msg = color.parse_color_codes_to_tags(msg)

	return msg


def escape(msg):
	"""	Converts special characters in msg and returns
		the new string. This function should only
		be used in combination with HTMLBuffer.
	"""
	msg = _escape_ml(msg)

	msg = msg.replace(chr(2), "<sb/>") # bold-char
	msg = msg.replace(chr(31), "<su/>") # underline-char

	msg = color.parse_color_codes_to_tags(msg)

	return msg

