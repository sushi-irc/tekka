""" provide functions for history handling.
	note that history stuff is only possible
	if maki is not running remote.
"""
import os
from ..com import sushi
from ..typecheck import types

FILEPATTERN= re.compile(r'([0-9]+)-([0-9]+)\.txt')
DATEPATTERN= re.compile(r'[(0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):([0-9]+)')

def get_log_dir():
	return sushi.config_get("directories","logs")


def get_available_servers():
	""" return a list with all servers containing logs """
	if sushi.remote:
		return []

	log_dir = get_log_dir()

	return [dir for dir in os.listdir(log_dir) if os.path.isdir(dir)]


@types(server=basestring)
def get_available_conversations(server):
	""" return a list with all available logged channels/queries """
	if sushi.remote or not server:
		return []

	log_dir = os.path.join(get_log_dir(), server)

	if not os.path.exists(log_dir):
		return []

	return [dir for dir in os.listdir(log_dir) if os.path.isdir(dir)]


@types(server=basestring, target=basestring)
def get_available_logs(server, target):
	""" return a list with all available logs for the target """
	if sushi.remote or not server or not basestring:
		return []

	log_dir = os.path.join(get_log_dir(), server, target)

	if not os.path.exists(log_dir):
		return []

	return [f for f in os.listdir(log_dir) if FILEPATTERN.match(f)
											and os.path.isfile(f)]

@types(log_file=basestring)
def get_log_date(log_file):
	""" return (year,month) tuple """
	match = FILEPATTERN.group(log_file)

	if not match:
		return ""

	return match.groups()



