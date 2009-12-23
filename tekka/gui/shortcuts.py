

def update_servertree_shortcuts():
	"""	Iterates through the TreeModel
		of the server tree and sets 9
		shortcuts to tabs for switching.
	"""
	tabList = tabs.get_all_tabs()
	st = widgets.get_widget("serverTree")

	for i in range(1, 10):
		removeShortcut(gui.accelGroup, st, "<alt>%d" % (i))

	c = 1
	for tab in tabList:
		if c == 10:
			break

		if (tab.is_server()
		and not config.get("tekka", "server_shortcuts")):
			continue

		addShortcut(gui.accelGroup, st, "<alt>%d" % (c),
			lambda w, s, p: tabs.switch_to_path(p), tab.path)

		c+=1


