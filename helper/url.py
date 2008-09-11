import re

urlExp = re.compile("(\w+)://[^ \t\"'<>]+[^ \t\"'<>,.)]")

def URLToTag(message):
	"""
		searches for an URL in message and sets an <a>-tag arround
		it, then returns the new string
	"""

	lastEnd = 0
	while True:
		match = urlExp.search(message, lastEnd)
		if not match:
			break
		mStart = match.start()
		mEnd = match.end()

		lastEnd = mStart

		url = message[mStart:mEnd]

		tagStart="<a href='%s'>" % url
		tagEnd = "</a>"

		msgStart = message[0:mStart]
		msgEnd = message[mEnd:]

		newUrl = tagStart + url + tagEnd
		message = msgStart + newUrl + msgEnd

		lastEnd += len(tagStart)+len(tagEnd)+len(url)
	return message

