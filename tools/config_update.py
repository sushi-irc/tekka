"""
tool for updating old non-json configurations
to json configurations.
"""

import sys

from tekka import config

from tekka.helper import escape

config.setup()

def iterSects():
	for section in config.config_parser.sections():
		for (name, value) in config.config_parser.items(section):
			yield section, name, value

changes = 0

for section, name, value in iterSects():
	if value.count(",") > 1 and value[0] != "[": # got a list in !json
		# convert to list via old stuff
		l = escape.unescape_split(",", value)
		config.set_list(section, name, l)
		changes += 1
		print "Updated '%s'." % (name,)

if changes == 0:
	print "No changes. Config is good."
	sys.exit(0)

while True:
	print "Write changes? (y|n) View result? (v)"
	try:
		c = raw_input()
	except EOFError:
		print "unexpected end."
		sys.exit(1)
	else:
		if c == "y":
			config.write_config_file()
			break
		elif c == "v":
			cSection = None
			for section, name, value in iterSects():
				if cSection == None or cSection != section:
					print "Section %s" % (section)
					cSection = section
				print "%s = %s" % (name, value)
		else:
			print "Not writing."
			break
