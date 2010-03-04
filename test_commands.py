import command_handler as cmdh

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

	cmdh.cmd_connect(s, c, s.name)
	cmdh.cmd_nick(s, c, s.nick)
	cmdh.cmd_part(s, c, c.name)
	cmdh.cmd_join(s, c, c.name)
	cmdh.cmd_action(s, c, ["tests","arround"])
	cmdh.cmd_mode(s, c, [c.name, "+b", s.nick])
	cmdh.cmd_mode(s, c, [c.name, "-b", s.nick])
	cmdh.cmd_away(s, c, ["i","am","away","nao"])
	cmdh.cmd_back(s, c, [])
	cmdh.cmd_ctcp(s, c, [s.nick, "CTCPOHAI"])
	cmdh.cmd_names(s, c, [c.name])
	cmdh.cmd_notice(s, c, [s.nick, "NOTICEOHAI"])
	cmdh.cmd_message(s, c, [s.nick, "MESSAGEOHAI"])
	cmdh.cmd_list(s, c, [c.name])
	cmdh.cmd_stop_list(s, c, [])
	cmdh.cmd_raw(s, c, ["PRIVMSG","",":",s.nick,"","RAWOHAI"])
	cmdh.cmd_whois(s, c, [s.nick])
	cmdh.cmd_clear(s, c, [])

	# XXX: Not tested here:
	# - quit
	# - oper
	# - kick
	# - topic
	# - nickserv
