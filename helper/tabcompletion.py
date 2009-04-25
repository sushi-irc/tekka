# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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

import commands
import com
import config
import gui_control

# types identificating the current scroll position
(
NO_TYPE,
NICK_TYPE,
QUERY_TYPE,
CHANNEL_TYPE,
COMMAND_TYPE
) = range(5)

# cache of position
_current = {
"position":None,
"tab":None,
"type":NO_TYPE,
"needle":None,
"lastCompletion":None
}

def _reset(full=False):
	global _current
	_current["position"] = None
	_current["tab"] = None
	_current["type"] = NO_TYPE
	_current["needle"] = None
	_current["lastCompletion"] = None

def _appendMatch(entry, mode, text, word, match):
	"""
	Complete `word` in `text` with `match` and
	apply it to the input bar widget.
	Add separator too.
	"""
	if mode == "c":
		separator = config.get("tekka","command_separator", " ")

	elif mode == "n":
		separator = config.get("tekka","nick_seperator", ": ")

	new_text = text[0:entry.get_position()-len(word)] + match + separator + text[entry.get_position():]
#	text = text[:-len(word)] + match + separator

	print "text: '%s' word: '%s' match: '%s'" % (text,word,match)

	old_position = entry.get_position()
	entry.set_text(new_text)

	entry.set_position(old_position + len(match+separator) -len(word))

	global _current
	_current["lastCompletion"] = match + separator

def _removeLastCompletion(entry, text):
	""" this function assumes, we're on the position _after_
		the completion...
	"""
	lc = _current["lastCompletion"]

	print "Last completion was: '%s'" % (lc)

	# strip of the match, keep the needle:
	# 'n'<Tab> => 'nemo: ' => strip 'emo: '
	print "text = %s, position = %d last_complete: %d (%s), needle: %d (%s)" % (
		text, entry.get_position(), len(lc), lc, len(_current["needle"]), _current["needle"])
	needle = _current["needle"]
	skip = (entry.get_position() - len(lc)) + len(needle)
	new_text = text[:skip]+text[entry.get_position():]
	#text = text[:-(len(lc)-len(_current["needle"]))]

	print "Cleaned text is: '%s'" % (text)

	entry.set_text(new_text)
	entry.set_position(skip)

	return new_text

def stopIteration():
	"""
	Interrupt iteration.
	Resets cached data (like needle)
	"""
	_reset()
	#_current["needle"] = None

def complete(currentTab, entry, text):
	"""
	The user pressed tab after `text`.
	* If currentTab is a channel, find a suitable nickname
	* If currentTab is a query, find a suitable nickname matching
	  my and the other nickname
	* Find a matching channel name
	* Find a matching command
	If there are multiple matches:
	* show the matches as statically last line (if enabled in config)
	* iterate over the results by pressing tab
	The end of the iteration is determined outside in the key press
	event of the input bar. If another key except "Tab" is pressed,
	the iteration ends (stopIteration).

	TODO: generalize code, especially the section checks / match checks
	"""

	global _current

	if not text:
		return False

	if currentTab != _current["tab"]:
		# reset iteration, data is not up to date
		_reset()
		_current["tab"] = currentTab

	if _current["needle"]:
		# continue searching for `needle`
		word = _current["needle"]
		text = _removeLastCompletion(entry, text)
		print "Continue iterating! Needle is '%s'" % (word)

	else:
		# get the word to complete
		# "f|<tab> || f |<tab>"
		word = text[0:entry.get_position()].split(" ")[-1].strip()

		_current["needle"] = word

	print "word is: '%s'" % (word)

	if not word:
		return False

	match = None

	if currentTab and currentTab.is_channel():
		# look for nicks

		matches = currentTab.nickList.searchNick(word.lower())
		matches.sort(lambda x, y: cmp(x.lower(), y.lower())) # sort alphabetically

		if matches:
			if _current["type"] == NICK_TYPE:
				# continue iterating

				if _current["position"]+1 >= len(matches) or _current["position"] == None:
					# position too high or unset, set to 0
					_current["position"] = 0

				else:
					_current["position"] += 1

			else:
				# we have matches, reset the current type and position
				_current["type"] = NICK_TYPE
				_current["position"] = 0

			# TODO: print lastLine filled with contents of matches

			print "current position: %d and cp = '%d'" % (_current["position"], len(matches))
			match = matches[_current["position"]]

		if match:

			# if the word is in a sentence, use command
			# completion (only whitespace)
			if text.count(" ") >= 1:
				mode = "c"
			else:
				mode = "n"

			_appendMatch(entry, mode, text, word, match)

			return True

	elif currentTab and currentTab.is_query():
		# look for my nick or the other nick

		matches = [nick for nick in (currentTab.name, com.getOwnNick(currentTab.server)) if nick[:len(word)].lower() == word.lower()]

		if matches:
			if _current["type"] == QUERY_TYPE:
				# continue iterating

				if _current["position"]+1 >= len(matches) or _current["position"] == None:
					_current["position"] = 0

				else:
					_current["position"] += 1

			else:
				# set type to the current and begin iterating
				_current["type"] = QUERY_TYPE
				_current["position"] = 0

			match = matches[_current["position"]]

		if match:
			if text.count(" ") >= 1:
				mode = "c"
			else:
				mode = "n"

			_appendMatch(entry, mode, text, word, match)

			return True

	# ** no successful completion so far **

	# channel completion
	if (currentTab
		and not currentTab.is_server()
		and word[0] in com.sushi.support_chantypes(currentTab.server)):
		tabs = gui_control.tabs.getAllTabs()

		# find all matching tabs
		matches = [tab.name for tab in tabs
			if tab and tab.name[:len(word)].lower() == word.lower()]

		if matches:
			if _current["type"] == CHANNEL_TYPE:

				if _current["position"]+1 >= len(matches) or _current["position"] == None:
					_current["position"] = 0

				else:
					_current["position"] += 1

			else:
				_current["type"] = CHANNEL_TYPE
				_current["position"] = 0

			match = matches[_current["position"]]

		if match:
			_appendMatch(entry, "c", text, word, match)
			return True

	# *** command completion ***

	if word[0] != "/":
		return False

	needle = word[1:]
	matches = [cmd for cmd in commands._commands.keys()
		if cmd[:len(needle)].lower()==needle.lower()]

	if matches:
		if _current["type"] == COMMAND_TYPE:
			if _current["position"]+1 >= len(matches) or _current["position"] == None:
				_current["position"] = 0

			else:
				_current["position"] += 1

		else:
			_current["type"] = COMMAND_TYPE
			_current["position"] = 0

		match = matches[_current["position"]]

	if match:
		_appendMatch(entry, "c",text, word, "/"+match)

		return True

	return False
