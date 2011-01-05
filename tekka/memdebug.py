import subprocess
import os

def current_mem(s=""):
	if(s): print ">>>>> "+s
	args = ["ps", "-o", "pid,rss,cmd","-p","%d" % (os.getpid())]
	subprocess.call(args)
c = current_mem

def memdec(f):
	def dec(*args,**kwargs):
		current_mem("before exec of "+f.func_name)
		ret = f(*args,**kwargs)
		current_mem("after exec of "+f.func_name)
		return ret
	return dec
