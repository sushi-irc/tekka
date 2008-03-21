import dbus
from dbus.mainloop.glib import DBusGMainLoop

class tekkaCom(object):
	def __init__(self):
		dbus_loop = DBusGMainLoop()
		self.bus = dbus.SessionBus(mainloop=dbus_loop)
		self.proxy = None
		try:
			self.proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
		except dbus.exceptions.DBusException, e:
			print e
			print "Is maki running?"
		if self.proxy:
			self.bus.add_signal_receiver(self.readText, "message", "de.ikkoku.sushi.maki", "de.ikkoku.sushi", "/de/ikkoku/sushi")

	def sendText(self, widget):
		print "sendText: received from widget."
		print widget.get_text()
		# TODO: if text[0] == "/":....
		widget.set_text("")

	def readText(self, text):
		print "received"
		print text
	
