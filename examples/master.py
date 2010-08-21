#!/usr/bin/env python

import time
from SocketServer import ThreadingMixin, TCPServer, StreamRequestHandler
import pydysh

class Master(object):

	def __init__(self):
		self.master_server = None
		super(Master, self).__init__()
	
	def startMonitor(self, ips, port=9999):
		for ip in ips:
			print "%10.5f :: Using pydish to start up a slave" % time.time()
			#pydsh(python slave.py -master_ip 127.0.0.1 -master_port 8888)
			import os
			# This may need to be threaded for this local lame example
			os.popen("python slave.py -master_ip 127.0.0.1 -master_port 8888")
	
	def initMasterServer(ip, port=8888):
		if not self.master_server:
			self.master_server = MasterServer((ip, port), MasterRequestHandler)
	def server_forever():
		if self.master_server:
			self.master_server.serve_forever()

class MasterRequestHandler(StreamRequestHandler):
	def handle(self):
		print "%10.5f :: Handling request" % time.time()
		req = self.rfile.readline().strip()
		if req.startswith("explosion:"):
			slave_addr = tuple(req.split(":")[1:])
			slave_ip = slave_info[0]
			slave_port = slave_info[1]
			print "%10.5f :: EXPLOSION request from: %s" %(time.time(), str(slave_addr))
			# do any handling now
		else:
			pass

class MasterServer(ThreadingMixin, TCPServer):
	allow_reuse_addr = 1


if __name__ == "__main__":
	master = Master()
	master.initMasterServer("127.0.0.1", port=8888)
	master.startMonitor(["127.0.0.1"], port=9999)
	master.serve_forver()

