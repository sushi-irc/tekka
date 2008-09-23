import gtk.glade

widgets = None
com = None

RESPONSE_ADD = 1

def setup(dialogs):
	global widgets, com
	com = dialogs.com
	widgets = gtk.glade.XML(dialogs.config.get("gladefiles","dialogs"), "serverAdd")

def run():
	data = None

	dialog = widgets.get_widget("serverAdd")

	servernameInput = widgets.get_widget("serverAdd_Servername")
	serveraddressInput = widgets.get_widget("serverAdd_Serveradress")
	serverportInput = widgets.get_widget("serverAdd_Serverport")
	serverautoconnectInput = widgets.get_widget("serverAdd_Autoconnect")
	nicknameInput = widgets.get_widget("serverAdd_Nick")
	realnameInput = widgets.get_widget("serverAdd_Realname")
	nickservInput = widgets.get_widget("serverAdd_Nickserv")

	result = dialog.run()
	if result == RESPONSE_ADD:
		data = {}
		data["servername"] = servernameInput.get_text()
		data["address"] = serveraddressInput.get_text()
		data["port"] = serverportInput.get_text()
		data["nick"] = nicknameInput.get_text()
		data["name"] = realnameInput.get_text()
		data["nickserv"] = nickservInput.get_text()
		if serverautoconnectInput.get_active():
			data["autoconnect"] = "true"
		else:
			data["autoconnect"] = "false"
	dialog.destroy()

	return data


