import sys
import socket
from threading import Thread

read_t = None
try:
	s = socket.socket(socket.AF_INET)
	s.connect(("localhost", 6667))
except BaseException as e:
	print "Connection failed: %s" % (e)
	sys.exit(1)

def read_loop(s):
	_stop = False
	def stop():
		_stop = True
	read_loop.stop = stop

	last_line = ""

	while True:
		if _stop:
			break
		try:
			a = s.recv(4096)
		except BaseException as e:
			print "READ ERROR: %s" % (e)
			break
		i = a.find("PING :")
		if i>=0 and last_line[-1] == "\n" and (i==0 or a[i-1] == "\n"):
			j = a.find(" ", i+len("PING :"))
			pong_str = "PONG :%s" % (a[i+len("PING :"):j])
			try:
				s.send(pong_str + "\r\n")
			except BaseException as e:
				print "Error while sending: %s" % (e)
				break
			print "SENT PONG: %s" % (pong_str)
		else:
			print a
		last_line = a

def main():
	read_t = Thread(target = read_loop, args = (s,))
	read_t.start()

	last_input = ""

	while True:

		input = raw_input("Send: ")

		if input == "/quit":
			read_loop.stop()
			break
		elif input[0:len("/join")] == "/join":
			split = input.split(" ")
			input = "JOIN :%s" % (split[1])
		elif input[0:len("/init")] == "/init":
			split = input.split(" ")
			input = "USER %s 0 0 0\r\nNICK %s" % (split[1], split[1])
			print "ASDASD = %s" %  (split[1])
		elif input[0:len("/long")] == "/long":
			from random import randint
			split = input.split(" ")
			sam = ["lorem","ipsum","foo","bar","baz"]
			pre = "PRIVMSG %s :" % (split[1])
			for i in range(int(split[2])):
				pre += sam[randint(0, len(sam)-1)]+" "
			input = pre

		elif input[0] == ".":
			split = input.split(" ")
			input = "PRIVMSG %s :%s" % (split[0][1:], " ".join(split[1:]))
		elif input == "=":
			input = last_input

		if input:
			try:
				s.send(input+"\r\n")
			except BaseException as e:
				print "Error while sending: %s" % (e)
				break
			last_input = input

try:
	main()
except BaseException as e:
	print "Error: %s" % (e)
	try:
		read_loop.stop()
	except: pass
	s.close()
	sys.exit(1)

