
test_string = "abc,de\\,,f\\,g,\\\\,h,i"
# result: ["abc","de,","f,g","\\\\","h","i"]

def get_escape_char_count(part, char):
	c = 0
	rev = range(len(part))
	rev.reverse()
	for i in rev:
		if part[i] == char:
			c += 1
		else:
			break
	return c

def unescape_splitted(separator, splitted, escape_char):
	escaped = []
	i = 0

	for split in splitted:
		if not split:
			continue

		if split[-1] == escape_char:
			count = get_escape_char_count(split, escape_char)

			if count % 2 != 0:
				# the , was escaped

				# merge this and the next split together.
				# add the escaped separator and remove the escape
				new_split = [split[:-1] + separator + splitted[i+1]]
				return escaped + unescape_splitted(
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
	escaped = unescape_splitted(separator, splitted, escape_char)
	return escaped

