import gtk
import gtk.glade

widgets = None
com = None

def setup(dialogs):
	global widgets, com
	com = dialogs.com
	widgets = gtk.glade.XML(dialogs.config.get("gladefiles","dialogs"),"serverEdit")

def run(server):
	serverdata = com.fetchServerInfo(server)

	serveraddressInput = widgets.get_widget("serverEdit_Address")
	serveraddressInput.set_text(serverdata["address"])

	serverportInput = widgets.get_widget("serverEdit_Port")
	serverportInput.set_text(serverdata["port"])

	servernameInput = widgets.get_widget("serverEdit_Realname")
	servernameInput.set_text(serverdata["name"])

	servernickInput = widgets.get_widget("serverEdit_Nick")
	servernickInput.set_text(serverdata["nick"])

	servernickservInput = widgets.get_widget("serverEdit_Nickserv")
	servernickservInput.set_text(serverdata["nickserv"])

	serverautoconnectInput = widgets.get_widget("serverEdit_Autoconnect")

	if serverdata["autoconnect"]:
		serverautoconnectInput.set_active(True)
	else:
		serverautoconnectInput.set_active(False)

	dialog = widgets.get_widget("serverEdit")
	result = dialog.run()

	newServer = {}

	if result == gtk.RESPONSE_OK:

		newServer["servername"] = serverdata["servername"]
		for i in ("address","port","name","nick","nickserv"):
			newServer[i] = eval("server%sInput.get_text()" % (i))

	dialog.destroy()

	return newServer

