
try:
	from sexy import SpellEntry as _SpellEntry
except ImportError:
	from gtk import Entry as _SpellEntry

class SpellEntry(_SpellEntry):

	__gtype_name__ = "SpellEntry"

	pass
