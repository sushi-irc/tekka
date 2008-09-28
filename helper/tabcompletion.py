import commands
import com
import config
import __main__ as main

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

def _appendMatch(mode, text, word, match):
	"""
	Complete `word` in `text` with `match` and
	apply it to the input bar widget.
	Add separator too.
	"""
	if mode == "c":
		separator = config.get("tekka","command_separator", " ")

	elif mode == "n":
		separator = config.get("tekka","nick_seperator", ": ")

	text = text[:-len(word)] + match + separator

	print "text: '%s' word: '%s' match: '%s'" % (text,word,match)

	inputBar = main.gui.getWidgets().get_widget("inputBar")
	inputBar.set_text(text)
	inputBar.set_position(len(text))

	global _current
	_current["lastCompletion"] = match + separator

def _removeLastCompletion(text):
	lc = _current["lastCompletion"]
	ib = main.gui.getWidgets().get_widget("inputBar")

	print "Last completion was: '%s'" %(lc)

	# strip of the match, keep the needle:
	# 'n'<Tab> => 'nemo: ' => strip 'emo: '
	text = text[:-(len(lc)-len(_current["needle"]))]

	print "Cleaned text is: '%s'" % (text)

	ib.set_text(text)
	ib.set_position(len(text))

	return text

def stopIteration():
	"""
	Interrupt iteration.
	Resets cached data (like needle)
	"""
	_reset()
	#_current["needle"] = None

def complete(currentTab, text):
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
		text = _removeLastCompletion(text)
		print "Continue iterating! Needle is '%s'" % (word)

	else:
		# get the word to complete
		words = text.strip(" ").split(" ")

		if not words:
			print "No words!"
			return

		word = words[-1]

		_current["needle"] = word
	
	print "word is: '%s'" % (word)

	if not word:
		return False

	match = None

	if currentTab and currentTab.is_channel():
		# look for nicks

		matches = currentTab.nickList.searchNick(word.lower())
		matches.sort() # sort alphabetically

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

			_appendMatch(mode, text, word, match)

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

			_appendMatch(mode, text, word, match)

			return True

	# ** no successful completion so far **

	# channel completion
	if word[0] in com.sushi.support_chantypes(currentTab.server):
		tabs = main.gui.tabs.getAllTabs()

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
			_appendMatch("c", text, word, match)
			return True

	# *** command completion ***

	if word[0] != "/":
		return False

	needle = word[1:]
	matches = [cmd for cmd in commands.commands.keys()
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
		_appendMatch("c",text, word, "/"+match)

		return True

	return False
