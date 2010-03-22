""" provide functions for history handling.
	note that history stuff is only possible
	if maki is not running remote.
"""
import re
import os
from ..com import sushi
from ..typecheck import types

FILEPATTERN= re.compile(r'([0-9]+)-([0-9]+)\.txt')
DATEPATTERN= re.compile(r'^([0-9]+)-([0-9]+)-([0-9]+) ([0-9]+):([0-9]+):([0-9]+)')

def get_log_dir():
	return sushi.config_get("directories","logs")


def get_available_servers():
	""" return a list with all servers containing logs """
	if sushi.remote:
		return []

	log_dir = get_log_dir()

	return [dir for dir in os.listdir(log_dir)]


@types(server=basestring)
def get_available_conversations(server):
	""" return a list with all available logged channels/queries """
	if sushi.remote or not server:
		return []

	log_dir = os.path.join(get_log_dir(), server)

	if not os.path.exists(log_dir):
		return []

	return [dir for dir in os.listdir(log_dir) if os.path.isdir(
											   os.path.join(log_dir, dir))]


@types(server=basestring, target=basestring)
def get_available_logs(server, target):
	""" return a list with all available logs for the target """
	if sushi.remote or not server or not basestring:
		return []

	log_dir = os.path.join(get_log_dir(), server, target)

	if not os.path.exists(log_dir):
		return []

	return [f for f in os.listdir(log_dir) if FILEPATTERN.match(f)
											and os.path.isfile(
												os.path.join(log_dir, f))]

@types(log_file=basestring)
def get_log_date(log_file):
	""" return (year,month) tuple """
	match = FILEPATTERN.match(log_file)

	if not match:
		return ""

	return match.groups()


@types(fd=file)
def parse_day_offsets(fd):
	offsets = {}

	start = fd.tell()
	offset = fd.tell()
	last_day = 0

	for line in fd:
		match = DATEPATTERN.match(line)

		if not match:
			continue

		(year, month, day, hour, minute, second) = match.groups()

		if day != last_day:
			offsets[(year, month, day)] = (start, offset)
			last_day = day
			start = offset

		offset += len(line)

	return offsets
