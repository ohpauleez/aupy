#!/usr/bin/env python

from __future__ import with_statement
import socket
import time
import threading
#import proc
import logexplode

class SlaveMonitor(object):
	""" This is the dumb version of the slave monitor.
	Rather than perform utility checks here, it merely just
	reports back log write information.  The Master will determine
	if the reported information indicates a log explosion and then
	take action"""

	def __init__(self, ip, master_ip, master_port=8888, port=9999):
		self.master_ip = master_ip
		self.master_port = master_port
		self.ip = ip
		self.port = port
		self.exploder = logexplode.LogExploder()
		#self.exploder.write_and_explode(max_normal_writes=20)
		t = threading.Thread(target=self.exploder.write_and_explode, kwargs={'max_normal_writes':20})
		t.start()
		super(SlaveMonitor, self).__init__()
	
	def monitorLog(self, log_file):
		try:
			time.sleep(2)
			while True:
				# Get a log report
				try:
					self.slave_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					self.slave_socket.connect((self.master_ip, self.master_port))
				except socket.gaierror, e:
					print "Address-related error during connection: %s" % e
					self.slave_socket = None
				except socket.error, e:
					print "General connection or socket creation error: %s" % e
					self.slave_socket = None
				with open(log_file) as f:
					total_lines = len(f.readlines())
					print "TOTAL LINES:", total_lines
				report_str = "%10.5f:log utility:%d:%s:%d" % (time.time(), total_lines, self.ip, self.port)
				# send it to the master, ife we have a socket
				if self.slave_socket:
					try:
						self.slave_socket.sendall(report_str)
						self.slave_socket.close()
					except socket.error, e:
						print "Errors on sending information to the master: %s" % e
						# do nothing more, the socket will be reset the next time around
					self.slave_socket = None
				time.sleep(1)
		except KeyboardInterrupt:
			if self.slave_socket:
				try:
					self.slave_socket.shutdown()
				except socket.error, e:
					print "A socket related error occured on cleanup: %s" % e
				except Exception, e:
					print "A general exception occured on cleanup: %s" %e
				self.slave_socket = None



if __name__ == "__main__":
	import sys
	import getopt
	args = sys.argv[1:]
	optlist, args = getopt.getopt(args, "v", ["master_ip", "master_port"])
	optlist = dict(optlist)
	if optlist.get("v"):
		print "Dumb slave, smart master: FAKE LOCAL-ONLY (NO PYDSH)"
		sys.exit(0)
	master_ip = optlist.get("master_ip", "127.0.0.1")
	master_port = optlist.get("master_port", 8888)
	sm = SlaveMonitor(ip="127.0.0.1", master_ip=master_ip, master_port=master_port, port=9999)
	sm.monitorLog("explode.log")

