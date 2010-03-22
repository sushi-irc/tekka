from tekka.helper import history

def start_test(gui):
	def dprint(*x,**y):
		gui.mgmt.myPrint(*x,**y)

	dprint("get_log_dir()")
	dprint("%s" % history.get_log_dir())
	dprint("get_available_servers()")
	dprint("%s" % history.get_available_servers())
	dprint("get_available_conversations('euIRC')")
	dprint("%s" % history.get_available_conversations('euIRC'))
	dprint("get_available_logs('euIRC','#bsdunix')")
	dprint("%s" % history.get_available_logs('euIRC', '#bsdunix'))


