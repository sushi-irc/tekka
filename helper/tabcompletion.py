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
	"position": None,
	"tab": None,
	"type": NO_TYPE,
	"needle": None,
	"lastCompletion": None
}

def _reset_iteration():
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
# FIXME: this mode stuff is so wrong..
	if mode == "c":
		separator = config.get("tekka","command_separator", " ")

	elif mode == "n":
		separator = config.get("tekka","nick_seperator", ": ")

	# old text without needle + new_word + separator + rest
	new_text = text[0:entry.get_position()-len(word)] + \
		match + \
		separator + \
		text[entry.get_position():]

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

	if lc == None:
		return text

	# strip of the match, keep the needle:
	# 'n'<Tab> => 'nemo: ' => strip 'emo: '
	print "text = %s, position = %d last_complete: " \
		"%d (%s), needle: %d (%s)" % (
		text, entry.get_position(),
		len(lc), lc,
		len(_current["needle"]),
		_current["needle"])

	needle = _current["needle"]
	skip = (entry.get_position() - len(lc)) + len(needle)
	new_text = text[:skip]+text[entry.get_position():]

	print "Cleaned text is: '%s'" % (text)

	entry.set_text(new_text)
	entry.set_position(skip)

	return new_text

def _raise_position(matches, i_type):
	if _current["type"] == i_type:
		# continue iterating
		if (_current["position"]+1 >= len(matches)
			or _current["position"] == None):
			_current["position"] = 0

		else:
			_current["position"] += 1

	else:
		# set type to the current and begin iterating
		_current["type"] = i_type
		_current["position"] = 0

def _match_nick_in_channel(tab, word):
	matches = tab.nickList.searchNick(word.lower())
	# sort nicks alphabetically
	matches.sort(lambda x, y: cmp(x.lower(), y.lower()))

	if matches:
		_raise_position(matches, NICK_TYPE)
		print "current position: %d and cp = '%d'" % (
			_current["position"], len(matches))

		return matches[_current["position"]]
	return None

def _match_nick_in_query(tab, word):
	matches = [nick for nick in (currentTab.name, com.getOwnNick(currentTab.server)) if nick[:len(word)].lower() == word.lower()]

	if matches:
		_raise_position(matches, QUERY_TYPE)
		return matches[_current["position"]]
	return None

def _match_channel(word):
	tabs = gui_control.tabs.getAllTabs()

	# find all matching tabs
	matches = [tab.name for tab in tabs
		if tab and tab.name[:len(word)].lower() == word.lower()]

	if matches:
		_raise_position(matches, CHANNEL_TYPE)
		return matches[_current["position"]]
	return None

def _match_command(word):
	matches = [cmd for cmd in commands._commands.keys()
	if cmd[:len(word)].lower()==word.lower()]

	if matches:
		_raise_position(matches, COMMAND_TYPE)
		return matches[_current["position"]]
	return None

def stopIteration():
	""" user does not want any more results, stop the iteration.
		This is the case if, for example, the tab is switched or
		the input bar is activated.
	"""
	_reset_iteration()

def complete(currentTab, entry, text):
	""" search for the last typed word and try to
		complete it in the following order:
		- search for a suitable nick in the channel (if tab is a channel)
		- search for a suitable nick in the query (if tab is a query)
		- search for a suitable command (if the first letter is a '/')
		- search for a suitable channel (if the first letter is
		  a valid channel prefix)

		If one of the searches matches, this function returns True.
		If no search matches, False is returned.

		The function checks, if the word searched for was the
		same as last time. So if complete is called another
		time, it will continue searching and using the next
		result to the one before.
	"""

	global _current

	if not text:
		return False

	if currentTab != _current["tab"]:
		# reset iteration, data is not up to date.
		# start new iteration, then
		_reset_iteration()
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

		match = _match_nick_in_channel(currentTab, word)

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

		match = _match_nick_in_query(currentTab, word)

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
		and word[0] in com.sushi.support_chantypes(currentTab.server)):

		match = _match_channel(word)

		if match:
			_appendMatch(entry, "c", text, word, match)
			return True

	# *** command completion ***

	if word[0] == "/":

		match = _match_command(word[1:])

		if match:
			_appendMatch(entry, "c",text, word, "/"+match)
			return True

	return False
