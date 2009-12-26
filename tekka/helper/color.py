"""
Copyright (c) 2009 Marian Tietz
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

"""
IRC color specifications
"""

import re
import gtk

from .. import config
from ..typecheck import types

from . import code
from . import escape

from ..lib import contrast
from .. import gui

COLOR_PATTERN = "([0-9]{1,2})(,[0-9]{1,2}){0,1}.*"
COLOR_TABLE =  {
			 0: contrast.CONTRAST_COLOR_WHITE,
			 1: contrast.CONTRAST_COLOR_BLACK,
			 2: contrast.CONTRAST_COLOR_BLUE,
			 3: contrast.CONTRAST_COLOR_DARK_GREEN,
			 4: contrast.CONTRAST_COLOR_DARK_RED,
			 5: contrast.CONTRAST_COLOR_LIGHT_BROWN,
			 6: contrast.CONTRAST_COLOR_PURPLE,
			 7: contrast.CONTRAST_COLOR_ORANGE,
			 8: contrast.CONTRAST_COLOR_YELLOW,
			 9: contrast.CONTRAST_COLOR_LIGHT_GREEN,
			10: contrast.CONTRAST_COLOR_CYAN,
			11: contrast.CONTRAST_COLOR_AQUA,
			12: contrast.CONTRAST_COLOR_LIGHT_BLUE,
			13: contrast.CONTRAST_COLOR_MAGENTA,
			14: contrast.CONTRAST_COLOR_GREY,
			15: contrast.CONTRAST_COLOR_LIGHT_GREY
		}

@types (msg = basestring)
def parse_color_codes_to_tags(msg):
	""" Parse the mIRC color format ^Cn[,m] and convert it
		to the intern handled <font></font> tag.
		Convert the numbers n and m into contrast color codes
		and use them as foreground/background.
	"""
	def get_gdk_color(ccolor):
		bg_color = gui.widgets.get_widget("output").\
			get_style().base[gtk.STATE_NORMAL]
		return contrast.contrast_render_foreground_color(
			bg_color, ccolor)

	last_i = -1
	count = 0 # openend <font>

	# initialize attributes self.pattern / self.color_table
	self = code.init_function_attrs(
		parse_color_codes_to_tags,

		pattern 	= re.compile(chr(3)+COLOR_PATTERN),
		color_table = COLOR_TABLE)

	while True:
		try:
			i = msg.index(chr(3), last_i+1)
		except ValueError:
			break

		match = self.pattern.match(msg[i:i+6])

		if match:
			groups = match.groups()
			tag = "<span"

			if count != 0:
				# close the previous color
				tag = "</span>" + tag
				count -= 1

			try:
				fg = self.color_table[int(groups[0])]
				fg = get_gdk_color(fg)
			except (KeyError, TypeError):
				fg = None
			else:
				tag += " foreground='%s'" % fg

			try:
				bg = self.color_table[int(groups[1][1:])]
				bg = get_gdk_color(bg)
			except (KeyError, TypeError):
				bg = None
			else:
				tag += " background='%s'" % bg

			tag += ">"
			skip_len = 1 + (groups[0] and len(groups[0]) or 0) \
				+ (groups[1] and len(groups[1]) or 0)
			msg = msg[:i] + tag + msg[i+skip_len:]

			count += 1

		else:
			if count > 0:
				# single ^C, if there's an open tag, close it
				msg = msg[:i] + "</span>" + msg[i+1:]
				count -= 1

		last_i = i

	if count != 0:
		# make sure the <font> is closed.
		msg = msg + "</span>"

	return msg

@types (s = basestring)
def parse_color_codes_to_markups(s):
	""" convert color codes to color markups (%C) and escape
		every % in s with %%.
	"""
	s = s.replace("%", "%%")
	return s.replace(chr(3), "%C")

@types (s = basestring)
def parse_color_markups_to_codes(s):
	""" split s for %C markups and parse the numbers following.
		After parsing, return the new string.
	"""
	s_split = escape.unescape_split("%C", s, escape_char="%")
	return chr(3).join(s_split)

@types (nick = basestring)
def get_nick_color(nick):
	"""
		Returns a static color for the nick given.
		The returned color depends on the color mapping
		set in config module.
	"""
	def pick_nick_color(colors, nick):
		return colors[sum([ord(n) for n in nick]) % len(colors)]

	if not config.get_bool("tekka","color_text"):
		return

	if not config.get_bool("colors", "nick_contrast_colors"):
		# pick a color out of the user defined list

		colors = config.get_list("colors", "nick_colors", [])
		color = pick_nick_color(colors, nick)

		return color
	else:
		# pick a contrast color

		bg_color = gui.widgets.get_widget("output")\
			.get_style().base[gtk.STATE_NORMAL]
		color = pick_nick_color(contrast.colors[:-1], nick)
		r = contrast.contrast_render_foreground_color(bg_color, color)

		return r

@types (nick = basestring)
def get_text_color(nick):
	"""
		Same as color.get_nick_color but for text and defaults
		to another value (text_message)
	"""
	if not config.get_bool("tekka","color_text"):
		return

	colors = contrast.colors[:-1]
	if not colors or not config.get_bool("tekka","color_nick_text"):
		return config.get("colors","text_message","#000000")

	bg_color = gui.widgets.get_widget("output").get_style().\
		base[gtk.STATE_NORMAL]

	color = colors[sum([ord(n) for n in nick]) % len(colors)]

	r = contrast.contrast_render_foreground_color(bg_color, color)
	return r

@types (text = basestring)
def strip_color_codes(text):
	""" strip all color codes (chr(3)) and the following numbers """
	l = []

	for w in text.split(chr(3)):
		new_start = 0

		# check if there's a pair of numbers or a single one
		try:
			int(w[0:2])
		except ValueError:
			try:
				int(w[0:1])
			except ValueError:
				pass
			else:
				new_start += 1
		else:
			new_start += 2

		# look for , if there was a number found before
		if new_start != 0 and w[new_start:new_start+1] == ",":
			# if a number is given, remove it including the ,
			try:
				int(w[new_start+1:new_start+3])
			except ValueError:
				try:
					int(w[new_start+1:new_start+2])
				except ValueError:
					pass
				else:
					new_start += 2
			else:
				new_start += 3

		l.append(w[new_start:])
	return "".join(l)
