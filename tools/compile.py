import compileall
import sys

if len(sys.argv) == 1:
	print >> sys.stderr, "Usage: %s <dir>" % (sys.argv[0])
else:
	compileall.compile_dir(sys.argv[1])
