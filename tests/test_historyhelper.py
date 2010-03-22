import os
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
	dprint("get_log_data('2009-13.txt')")
	dprint("%s" % (history.get_log_date('2009-13.txt'),))

	fpath = os.path.join(history.get_log_dir(), 'euIRC', '#bsdunix',
						'2009-03.txt')
	dprint("parse_day_offsets(%s)" % (fpath))
	dprint("%s" % (history.parse_day_offsets(file(fpath,"r")),))

