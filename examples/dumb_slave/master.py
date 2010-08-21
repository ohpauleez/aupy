#!/usr/bin/env python
from __future__ import with_statement
import time
from SocketServer import ThreadingMixIn, TCPServer, StreamRequestHandler
#import pydysh
from aupy2 import Utility

class Master(object):

	def __init__(self):
		self.master_server = None
		super(Master, self).__init__()
	
	def startMonitor(self, ips, port=9999):
		for ip in ips:
			print "%10.5f :: Using pydish to start up a slave" % time.time()
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


class MasterRequestHandler(StreamRequestHandler):
	def logUtility(self, log_info):
		log_info = eval(log_info) # log info is a string: "False"
		if not log_info:
			print "%10.5f :: LOG EXPLOSION" % time.time()
		return log_info
	def explosionHandler(self, slave_addr):
		print "%10.5f :: handling (callback) from the explosion on %s" % (time.time(), str(slave_addr))
		
	def handle(self):
		print "%10.5f :: Handling request" % time.time()
		req = self.rfile.readline().strip()
		req = req.split(":")
		if req[1] == "log utility":
			print "%10.5f :: Log request" % time.time()
			slave_addr = tuple(req[-2:])
			slave_ip = slave_addr[0]
			slave_port = slave_addr[1]
			log_info = req[2]
			try:
				with Utility.contextUtility(self.logUtility, log_info, evalFunc=bool, 
						utilityCallback=self.explosionHandler, utilityCallbackArgs=[(slave_addr)]) as status:
					if not isinstance(status, Utility.UtilityError):
						print "%10.5f :: No Explosion Before :: slave->%s" %(time.time(), str(slave_addr))
			except RuntimeError:
				print "\tSEE TODO: yield was never reached in the generator" #TODO: replace contexts with either wrappers or classes
		else:
			pass

class MasterServer(ThreadingMixIn, TCPServer):
	allow_reuse_addr = 1


if __name__ == "__main__":
	master = Master()
	master.initMasterServer("127.0.0.1", port=8888)
	master.startMonitor(["127.0.0.1"], port=9999)
	try:
		master.serve_forever()
	except KeyboardInterrupt:
		print "\nGodspeed and Rock 'n Roll!"

