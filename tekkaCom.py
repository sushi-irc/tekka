import dbus
from dbus.mainloop.glib import DBusGMainLoop

"""

Rausfinden auf welchem Server wir senden
Rausfinden auf welchem Channel wir senden
Rausfinden was wir senden wollen


"""

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
		
		if not self.proxy:
			print "No connection to maki. Aborting."
			widget.set_text("")
			return

		text = widget.get_text()

		if text[0] == "/" and text[1] != "/":
			self.parseCommand(text[1:])
		else:
			self.proxy.say("")
		widget.set_text("")

	def readText(self, text):
		print "received"
		print text
	
	def connectServer(self, widget):
		print "would connect"

	def newServer(self, newServer):
		print "adding new server to maki"
