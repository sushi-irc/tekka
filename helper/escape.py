# coding: UTF-8
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

test_string = "abc,de\\,,f\\,g,\\\\,h,i"
# result: ["abc","de,","f,g","\\\\","h","i"]

def _get_escape_char_count(part, char):
	c = 0
	rev = range(len(part))
	rev.reverse()
	for i in rev:
		if part[i] == char:
			c += 1
		else:
			break
	return c

def _unescape_splitted(separator, splitted, escape_char):
	escaped = []
	i = 0

	for split in splitted:
		if not split:
			escaped.append(split)
			continue

		if split[-1] == escape_char:
			count = _get_escape_char_count(split, escape_char)

			if count % 2 != 0:
				# the , was escaped

				# merge this and the next split together.
				# add the escaped separator and remove the escape
				new_split = [split[:-1] + separator + splitted[i+1]]
				return escaped + _unescape_splitted(
					separator,
					new_split + splitted[i+2:],
					escape_char)
			else:
				escaped.append(split)
		else:
			escaped.append(split)
		i+=1
	return escaped


def unescape_split(separator, tosplit, escape_char="\\"):
	splitted = tosplit.split(separator)
	escaped = _unescape_splitted(separator, splitted, escape_char)
	return escaped

def escape_join (separator, list, escape_char="\\"):
	return separator.join([
		item.replace(escape_char, 2*escape_char)\
		.replace(separator,escape_char+separator) for item in list if item])
