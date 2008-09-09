import tekka

class pluginNP(tekka.plugin):
	
	def __init__(self, name):
		tekka.plugin.__init__(self, name)

		self.register_command("np", self.np_command)

	def np_command(self, currentServer, currentTab, args):
		self.get_dbus_interface().message(currentServer.name, currentTab.name, "np: Bla - blub")


def load():
	np = pluginNP("np")
