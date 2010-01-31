"""
Copyright (c) 2009-2010 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
	notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
	notice, this list of conditions and the following disclaimer in the
	documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

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

