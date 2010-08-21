#!/usr/bin/env python
from __future__ import with_statement
import time
import sys
from SocketServer import ThreadingMixIn, TCPServer, StreamRequestHandler
#import pydysh
from aupy2 import Utility

class Master(object):

	def __init__(self):
		self.master_server = None
		super(Master, self).__init__()
	
	def startMonitor(self, ips, port=9999):
		for ip in ips:
			print "%10.5f :: Using pydsh to start up a slave" % time.time()
			#pydsh(python slave.py -master_ip 127.0.0.1 -master_port 8888)
			import os, threading
			t = threading.Thread(target=os.popen, args=["python slave.py --master_ip 127.0.0.1 --master_port 8888"])
			t.start()
	
	def initMasterServer(self, ip, port=8888):
		if not self.master_server:
			self.master_server = MasterServer((ip, port), MasterRequestHandler)
	def serve_forever(self):
		if self.master_server:
			self.master_server.serve_forever()
		else:
			raise Exception("You need to init the server first")

past_log_writes = None
past_timestamp = None
past_rate = 1.0

class MasterRequestHandler(StreamRequestHandler):
	def logUtility(self, timestamp, log_writes):
		global past_log_writes, past_timestamp, past_rate
		if not past_timestamp:
			print "FIRST"
			past_log_writes = log_writes
			past_timestamp = timestamp
			past_rate = 1.0
			return True
		
		print "old write", past_log_writes
		print "new write", log_writes
		print "old time", past_timestamp
		print "new time", timestamp
		delta_writes = log_writes - past_log_writes
		past_log_writes = log_writes
		delta_time = timestamp - past_timestamp
		past_timestamp = timestamp
		print "delta write: %d  delta t: %f" % (delta_writes, delta_time)
		rate = float(delta_writes)/delta_time
		delta_rate = rate - past_rate
		past_rate = rate
		print "%10.5f :: Delta rate = %f" % (time.time(), delta_rate)

		if delta_rate > 2:
			print "%10.5f :: LOG EXPLOSION" % time.time()
			return False
		return delta_rate or True

	def explosionHandler(self, slave_addr):
		print "%10.5f :: handling (callback) from the explosion on %s" % (time.time(), str(slave_addr))
		#sys.exit(0)
		
	def handle(self):
		print "%10.5f :: Handling request" % time.time()
		req = self.rfile.readline().strip()
		req = req.split(":")
		if req[1] == "log utility":
			print "%10.5f :: Log request" % time.time()
			slave_addr = tuple(req[-2:])
			slave_ip = slave_addr[0]
			slave_port = slave_addr[1]
			log_writes = int(req[2])
			timestamp = float(req[0])
			print "WE GOT TIME:", timestamp
			try:
				with Utility.contextPreUtility(self.logUtility, timestamp, log_writes, evalFunc=bool, 
						utilityCallback=self.explosionHandler, utilityCallbackArgs=[(slave_addr)]) as status:
					if not isinstance(status, Utility.UtilityError):
						print "%10.5f :: No Explosion Before :: slave->%s" %(time.time(), str(slave_addr))
			except RuntimeError:
				# you should never see this.. you should check "status" for an exception
				print "\tSEE TODO: yield was never reached in the generator"
		else:
			pass

class MasterServer(ThreadingMixIn, TCPServer):
	allow_reuse_addr = 1
	def handle_error(self, request, client_address):
		#TODO We need to exit and stop everything when we see the error from handler's sys.exit() call
		#raise Exception("Most Likely An Explosion")
		#sys.exit(0)
		pass


if __name__ == "__main__":
	master = Master()
	master.initMasterServer("127.0.0.1", port=8888)
	master.startMonitor(["127.0.0.1"], port=9999)
	try:
		master.serve_forever()
	except KeyboardInterrupt:
		print "\nGodspeed and Rock 'n Roll!"
		sys.exit(0)
	except:
		sys.exit(0)

