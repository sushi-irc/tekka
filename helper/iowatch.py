class IOWatch(object):

	def __init__(self, callbacks):
		self.callbacks = callbacks
		self.closed = False
		self.encoding = "UTF-8"

	def _call_callbacks(self, msg):
		for cb in self.callbacks:
			cb(msg)

	def write(self, s):
		self._call_callbacks(s)

	def writelines(self, seq):
		for s in seq:
			self._call_callbacks(s)

	def close(self):
		pass

	def fileno(self):
		return -1

	def flush(self):
		pass

	def isatty(self):
		return True

