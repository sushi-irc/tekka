import tekka

class testPlugin(tekka.plugin):

	def __init__(self, name):
		tekka.plugin.__init__(self, name)

		self.get_dbus_interface().connect_to_signal("message", self.messageFilter)

	def messageFilter(self, time, server, nick, channel, text):
		print "test: '%s'" % (text)

def load():
	test = testPlugin("test")

