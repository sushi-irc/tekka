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

