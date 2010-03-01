from tekka.typecheck import types

@types()
def test0(a):
	return True

@types(a = int, b = int)
def test1(a,b):
	return True

@types(a = str, b = str)
def test2(a,b):
	return True

@types(a = (unicode,str), b = (unicode,str))
def test3(a,b):
	return True

if __name__ == "__main__":
	def red(s): return "%s[31m%s%s[0m" % (chr(27),s,chr(27))
	def green(s): return "%s[32m%s%s[0m" % (chr(27),s,chr(27))

	def assert_raise(et, cs):
		try:
			print "Executing '%s'...\t" % (cs),
			eval(cs)

		except BaseException as e:
			if type(e) == et:
				print green("success")
				return

		print red("fail")


	assert( True == test0(1) )

	assert( True == test1(1,2) )
	assert_raise(TypeError, """test1(1.1,2.1)""")
	assert_raise(TypeError, """test1("1","2")""")

	assert( True == test2("a","b") )
	assert_raise(TypeError, """test2(1,2)""")
	assert_raise(TypeError, """test2(u"foo",u"bar")""")

	assert( True == test3(u"foo",u"bar") )
	assert( True == test3("foo", "bar") )
	assert_raise(TypeError, """test3(1,2)""")
	assert_raise(TypeError, """test3(1.0,2.0)""")
