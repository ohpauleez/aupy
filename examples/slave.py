#!/usr/bin/env python
from __future__ import with_statement
import socket
import time
import proc
import log_explosion
from aupy2 import Utility

class SlaveMonitor(object):
	
	def __init__(self, ip, master_ip, master_port=8888, port=9999):
		self.master_ip = master_ip
		self.master_port = master_port
		self.ip = ip
		self.port = port
		super(SlaveMonitor, self).__init__()
	
	def log_utility(self):
		#TODO pydoc comments
		#TODO replace with log_exploder + proc
		# Until we use real (or simulated) log explosions...
		print "%10.5f :: log utility..." % time.time()
		time.sleep(5) #simulate a log being written, and then exploding 5 seconds later...
		print "%10.5f :: LOG EXPLOSION" % time.time()
		raise Utility.UtilityError("Log explosion")
		# Return False as if the explosion just happened
		# we should never get here
		return False

	def log_callback(self):
		print "%10.5f :: Slave Calling back using a socket..." % time.time()
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.master_ip, self.master_port))
		s.send("explosion:%s:%d" %(self.ip, self.port))
		s.close()
		return True

	def monitorLog(self, log_file):
		with Utility.contextUtility(self.log_utility, evalFunc=bool, utilityCallback=self.log_callback) as status:
			while True:
				pass


if __name__ == "__main__":
	#TODO look at sys.args to get the master_ip and the master_port
	sm = SlaveMonitor(ip="127.0.0.1", master_ip="127.0.0.1", master_port=8888, port=9999)
	sm.monitorLog("some.log")

