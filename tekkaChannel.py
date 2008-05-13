
import tekkaGUI
import htmlbuffer

"""
Provides basic attributes like the outputbuffer
(default a htmlbuffer), the name of the tab and
a flag if a new message is received.
"""
class tekkaTab(object):
	def __init__(self, name, buffer=None):
		self.buffer = buffer or htmlbuffer.htmlbuffer()
		self.name = name
		self.newMessage = []

	# the output buffer
	def getBuffer(self):
		return self.buffer

	def setBuffer(self, buffer):
		self.buffer = buffer

	# the identifying name
	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	# there is a new message
	def getNewMessage(self):
		return self.newMessage

	def setNewMessage(self, type):
		if not type:
			self.newMessage = []
		try:
			self.newMessage.index(type)
		except:
			self.newMessage.append(type)

	# markup the string in due to the
	# set properties
	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name

class tekkaServer(tekkaTab):
	def __init__(self, name, buffer=None):
		tekkaTab.__init__(self, name, buffer)

		self.connected = False
		self.away = False
		self.awaymessage = ""

	# is the server connected
	def getConnected(self):
		return self.connected

	def setConnected(self,switch):
		self.connected = switch

	# we're away
	def getAway(self):
		return self.away

	def setAway(self, switch):
		self.away = switch

	def getAwayMessage(self):
		return self.awayMessage

	def setAwayMessage(self, msg):
		self.awayMessage = msg

	def markup(self):
		base = self.name
		if not self.connected:
			base = "("+base+")"
		if self.newMessage:
			base = "<b>"+base+"</b>"
		if self.away:
			base = "<i>"+base+"</i>"
		return base

class tekkaChannel(tekkaTab):
	def __init__(self, name, buffer=None, nicklist=None, topic=None, topicsetter=None):
		tekkaTab.__init__(self, name, buffer)

		self.nicklist = nicklist or tekkaGUI.tekkaNicklistStore()
		self.topic = topic or ""
		self.topicsetter = topicsetter or ""

		self.joined = False

	# the nicks in the channel
	def getNicklist(self):
		return self.nicklist

	def setNicklist(self, nicklist):
		self.nicklist = nicklist

	# what's the topic
	def getTopic(self):
		return self.topic or ""

	def setTopic(self, topic):
		self.topic = topic

	# who set the topic
	def getTopicsetter(self):
		return self.topicsetter

	def setTopicsetter(self, topicsetter):
		self.topicsetter = topicsetter

	# is the channel joined?
	def getJoined(self):
		return self.joined

	def setJoined(self, switch):
		self.joined = switch

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.joined:
			base = "("+base+")"

		if "action" in self.newMessage:
			italic = True
		if "message" in self.newMessage:
			bold = True
		if "highlightmessage" in self.newMessage and "highlightaction" in self.newMessage:
			foreground = "#DDDD00"
		elif "highlightmessage" in self.newMessage:
			foreground = "#DD0000"
		elif "highlightaction" in self.newMessage:
			foreground = "#00DD00"
		
		markup = "<span "
		if italic:
			markup += "style='italic' "
		if bold:
			markup += "weight='bold' "
		if foreground:
			markup += "foreground='%s'" % foreground
		markup += ">%s</span>" % base

		return markup
