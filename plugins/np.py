def npCommand(currentServer, currentChannel, args):
	"""
	"""
	getDBusInterface().message(currentServer.name, currentChannel.name, "np: blab - blub")

def __init__():
	registerCommand("np", npCommand)
