import gtk
import config
import lib.tab as tabs
from lib.gui_control import builder

widgets = None
active_tab = None

buttons = {
	"joinButton":"join",
	"partButton":"part",
	"quitButton":"quit",
	"kickButton":"kick",
	"nickButton":"nick",
	"modeButton":"mode"
}

messagetypes = {}

# fill types with mirrored buttons
for (key, val) in buttons.items():
	messagetypes[val] = key

def get_tab_category(tab):
	cat = ""
	if type(active_tab) == tabs.TekkaServer:
		cat = "server_%s" % (active_tab.name.lower())
	elif type(active_tab) == tabs.TekkaChannel:
		cat = "channel_%s_%s" % (active_tab.server.name.lower(),
			active_tab.name.lower())
	elif type(active_tab) == tabs.TekkaQuery:
		cat = "query_%s_%s" % (active_tab.server.name.lower(),
			active_tab.name.lower())
	return cat

def get_hidden_types(tab):
	cat = get_tab_category(tab)

	return {
		"hide_own": config.get_list(cat, "hide_own", []),
		"hide": config.get_list(cat, "hide", []) }

def check_empty_section(cat, data):
	if len(data["hide"]) == 0:
		config.unset(cat, "hide")

	if len(data["hide_own"]) == 0:
		config.unset(cat, "hide_own")

def apply_button_setting(button):
	cat = get_tab_category(active_tab)
	d = get_hidden_types(active_tab)
	mtype = buttons[button.get_property("name")]

	if not button.get_active():
		# remove entry
		try:
			d["hide"].remove(mtype)
		except ValueError:
			pass
	else:
		# add entry if not given
		try:
			d["hide"].index(mtype)
		except ValueError:
			d["hide"].append(mtype)

	if not config.has_section(cat):
		config.create_section(cat)

	config.set_list(cat, "hide", d["hide"])

	check_empty_section(cat, d)

def apply_own_button_setting(button):
	cat = get_tab_category(active_tab)
	d = get_hidden_types(active_tab)
	mtype = buttons[button.get_property("name")[:-4]]

	if not button.get_active():
		# remove own entry
		try:
			d["hide_own"].remove(mtype)
		except ValueError:
			pass
	else:
		# add entry
		try:
			d["hide_own"].index(mtype)
		except ValueError:
			d["hide_own"].append(mtype)

	if not config.has_section(cat):
		config.create_section(cat)
	print "set_list(%s, hide_own, %s)" % (cat, d["hide_own"])

	config.set_list(cat, "hide_own", d["hide_own"])

	check_empty_section(cat, d)

def apply_current_settings():
	d = get_hidden_types(active_tab)

	for mtype in d["hide"]:
		button = widgets.get_object(messagetypes[mtype])
		button.set_active(True)

	for mtype in d["hide_own"]:
		button = widgets.get_object(messagetypes[mtype]+"_own")
		button.set_active(True)

def run(current_tab):
	global active_tab

	def dialog_response_cb(dialog, id):
		dialog.destroy()

	dialog = widgets.get_object("hideDialog")

	if not dialog:
		raise Exception, "Hide dialog cannot be retrieved."

	active_tab = current_tab

	apply_current_settings()

	dialog.connect("response", dialog_response_cb)
	dialog.show_all()

def setup():
	global widgets

	widgets = builder.load_dialog("hide")

	if not widgets:
		raise Exception, "Couldn't load the dialog"

	sigdic = {
		"joinButton_toggled_cb": apply_button_setting,
		"partButton_toggled_cb": apply_button_setting,
		"quitButton_toggled_cb": apply_button_setting,
		"kickButton_toggled_cb": apply_button_setting,
		"nickButton_toggled_cb": apply_button_setting,
		"modeButton_toggled_cb": apply_button_setting,
		"joinButton_own_toggled_cb": apply_own_button_setting,
		"partButton_own_toggled_cb": apply_own_button_setting,
		"quitButton_own_toggled_cb": apply_own_button_setting,
		"kickButton_own_toggled_cb": apply_own_button_setting,
		"nickButton_own_toggled_cb": apply_own_button_setting,
		"modeButton_own_toggled_cb": apply_own_button_setting,

	}

	widgets.signal_autoconnect(sigdic)
