import tekka
import mpd

class pluginNP(tekka.plugin):
	
	def __init__(self, name):
		tekka.plugin.__init__(self, name)

		self.register_command("np", self.np_command)

	def np_command(self, currentServer, currentTab, args):
		client = mpd.MPDClient()
		client.connect("localhost", 6600)

		data = {"artist":"N/A","title":"N/A","album":"N/A"}
		data.update(client.currentsong())

		fstring = "np: %(artist)s - %(title)s" % data

		self.get_dbus_interface().message(currentServer.name, currentTab.name, fstring)

		client.disconnect()

def load():
	np = pluginNP("np")
