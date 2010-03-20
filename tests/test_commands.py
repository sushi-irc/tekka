import command_handler as cmdh

""" This file is more likely to find programming errors than
	to check logical flaws. It will NOT show you if a command
	acted correctly, it will only show if it's not faulty
	programmed.
"""

def start_test(gui):
	_commands = {
		"connect" : cmdh.cmd_connect,
		"nick" : cmdh.cmd_nick,
		"part" : cmdh.cmd_part,
		"join" : cmdh.cmd_join,
			"j" : cmdh.cmd_join,
		"me"   : cmdh.cmd_action,
		"kick" : cmdh.cmd_kick,
		"mode" : cmdh.cmd_mode,
		"topic": cmdh.cmd_topic,
		"quit" : cmdh.cmd_quit,
		"away" : cmdh.cmd_away,
		"back" : cmdh.cmd_back,
	"nickserv" : cmdh.cmd_nickserv,
		"ctcp" : cmdh.cmd_ctcp,
		"names" :  cmdh.cmd_names,
		"notice" : cmdh.cmd_notice,
		"msg" : cmdh.cmd_message,
		"oper" : cmdh.cmd_oper,
		"list" : cmdh.cmd_list,
		"raw" : cmdh.cmd_raw,
		"stoplist" : cmdh.cmd_stop_list,
		"whois" : cmdh.cmd_whois,
		"query":  cmdh.cmd_query,
		"clear":  cmdh.cmd_clear,
		"help":  cmdh.cmd_help
	}

	for (cmd,hdl) in _commands.items():
		gui.mgmt.myPrint("Testing %s with None args..." % (cmd))
		hdl(None, None, [])

	gui.mgmt.myPrint("Testing simple commands...")
	s,c = gui.tabs.get_current_tabs()

	gui.mgmt.myPrint("Testing with server %s and channel %s.\n"
					 "Server is connected: %s\n"
					 "Channel is query: %s\n"
					 "Channel is joined: %s\n" % (
					 	s, c,
					 	s and s.connected,
						c and c.is_query(),
						c and c.is_channel() and c.joined))

	gui.mgmt.myPrint("cmd_connect(%s)" % (s.name,))
	# Should do nothing if we're connected
	cmdh.cmd_connect(s, c, [s.name])

	gui.mgmt.myPrint("cmd_nick(%s)" % (s.nick,))
	# Should do nothing (nick change to the same nick)
	cmdh.cmd_nick(s, c, [s.nick])

	gui.mgmt.myPrint("cmd_part(%s)" % (c.name,))
	# Part the current channel
	cmdh.cmd_part(s, c, [c.name])

	gui.mgmt.myPrint("cmd_join(%s)" % (c.name,))
	# Should join the channel
	cmdh.cmd_join(s, c, [c.name])

	gui.mgmt.myPrint("cmd_action(%s)" % (["tests","arround"],))
	# Should print "<nick> tests arround"
	cmdh.cmd_action(s, c, ["tests","arround"])

	gui.mgmt.myPrint("cmd_mode(%s)" % ([c.name, "+b", s.nick],))
	# Should ban us
	cmdh.cmd_mode(s, c, [c.name, "+b", s.nick])

	gui.mgmt.myPrint("cmd_mode(%s)" % ([c.name, "-b", s.nick],))
	# Should unban us
	cmdh.cmd_mode(s, c, [c.name, "-b", s.nick])

	gui.mgmt.myPrint("cmd_away(%s)" % ("i am away now",))
	# Should set us away with the message "i am away nao"
	cmdh.cmd_away(s, c, ["i","am","away","nao"])

	gui.mgmt.myPrint("cmd_back()")
	# Should set us back
	cmdh.cmd_back(s, c, [])

	gui.mgmt.myPrint("cmd_ctcp(%s)" % ([s.nick, "CTCPOHAI"],))
	# should send us a CTCP message with content "CTCPOHAI"
	cmdh.cmd_ctcp(s, c, [s.nick, "CTCPOHAI"])

	gui.mgmt.myPrint("cmd_names(%s)" % (c.name,))
	# should print the NAMES list of the given channel
	cmdh.cmd_names(s, c, [c.name])

	gui.mgmt.myPrint("cmd_notice(%s)" % ([s.nick, "NOTICEOHAI"],))
	# Should send us a notice with the content "NOTICEOHAI"
	cmdh.cmd_notice(s, c, [s.nick, "NOTICEOHAI"])

	gui.mgmt.myPrint("cmd_message(%s)" % ([s.nick, "MESSAGEOHAI"],))
	# Should send us a message with the content "MESSAGEOHAI"
	cmdh.cmd_message(s, c, [s.nick, "MESSAGEOHAI"])

	gui.mgmt.myPrint("cmd_list(%s)" % (c.name,))
	# Should LIST the current channel
	cmdh.cmd_list(s, c, [c.name])

	gui.mgmt.myPrint("cmd_stop_list()")
	# Should do nothing or stop the listing from above (if still running)
	cmdh.cmd_stop_list(s, c, [])

	gui.mgmt.myPrint("RAW")
	# Should send a raw PRIVMSG to ourself
	cmdh.cmd_raw(s, c, ["PRIVMSG","",":",s.nick,"","RAWOHAI"])

	gui.mgmt.myPrint("cmd_whois(%s)" % (s.nick,))
	# Trigger whois on ourself
	cmdh.cmd_whois(s, c, [s.nick])

	gui.mgmt.myPrint("cmd_clear()")
	# Should clear all outputs
	cmdh.cmd_clear(s, c, [])

	# XXX: Not tested here:
	# - quit
	# - oper
	# - kick
	# - topic
	# - nickserv
