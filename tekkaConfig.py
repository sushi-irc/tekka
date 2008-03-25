

class tekkaConfig(object):
	def __init__(self):
		self.useExternalDBus = False
		self.busAdress = "tcp:host=192.168.1.101,port=3333"

		self.gladefiles = {}
		self.gladefiles["mainwindow"] = "mainwindow.glade"
		self.gladefiles["dialogs"] = "dialogs.glade"

		# TODO: parse config file ~/.sushi/tekka.conf
