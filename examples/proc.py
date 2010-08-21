#!/usr/bin/env python

from __future__ import with_statement
import time
import re
import os
import functools

if not os.path.isdir("/proc"):
	print "This only works for systems with /proc"
	import sys
	sys.exit(1)


def getStatTimes():
	# Get the stat file and read in the first line
	with open("/proc/stat", "r") as stat_file:
		timeList = stat_file.readline().split(" ")[2:6]
	timeList = map(int, timeList)
	return timeList

def deltaTime(interval, func, *args):
	# Get our x value you, sleep, and get the y value
	x = func.__call__(args) if args else func()
	time.sleep(interval)
	y = func.__call__(args) if args else func()
	# Subtract x from y to get the delta over the time interval
	if type(x) is dict:
		for key in x:
			y[key] -= x[key]
	elif type(x) is list:
		for i in xrange(len(x)):
			y[i] -= x[i]
	else:
		#(type(x) is int) or (type(x) is float)
		# Or a user defined object that supports __sub__
		y -= x
	return y

def getCPUDiff(dTimes):
	return 100 - (dTimes[-1] * 100.00 / sum(dTimes))
def getCPUPercent(interval):
	dTimes = deltaTime(interval, getStatTimes)
	return getCPUDiff(dTimes)
	
def getBytes(intveral, dev_name):
	dNet = deltaTime(interval, getNetInfoOnDev, dev_name)
	return dNet["bytes"]
	
def getThroughput(interval, dev_name):
	return getBytes(interval, dev_name)/interval
	
def getPackets(intverval, dev_name):
	dNet = deltaTime(interval, getNetInfoOnDev, dev_name)
	return dNet["packets"]

def getPacketsPerSec(interval, dev_name):
	return getPackets(interval, dev_name)/interval

def getNetInfoOnDev(dev_name):
	bytes = 0
	packets = 0
	#Get the network device files
	with open("/proc/net/dev", "r") as net_file:
		lines = net_fileile.readlines()
	# Parse it for the device we want (ie: dev_name)
	for line in lines:
		if line.startswith("  " + dev_name):
			# Get the information we want 
			parts[2] = parts[2].split(":")[-1]
			bytes = parts[2]
			packets = parts[3]
	return {"bytes":bytes, "packets":packets}

def getMemInfo():
	meminfo = dict.fromkeys(["cached", "cachedunits", "dirty", "dirtyunits", "anonpages", "anonpagesunits", "mapped", "mappedunits"])
	# read in the meminfo file and parse for keywords
	with open("/proc/meminfo", "r") as mem_file:
		lines = mem_file.readlines()

	for line in lines:
		if line.startswith("Cached"):
			line = line.split(" ")
			meminfo["cached"] = line[-2]
			meminfo["cachedunits"] = line[-1]
		elif line.startswith("Dirty"):
			line = line.split(" ")
			meminfo["dirty"] = line[-2]
			meminfo["dirtyunits"] = line[-1]
		elif line.startswith("AnonPages"):
			line = line.split(" ")
			meminfo["anonpages"] = line[-2]
			meminfo["anonpagesunits"] = line[-1]
		elif line.startswith("Mapped"):
			line = line.split(" ")
			meminfo["mapped"] = line[-2]
			meminfo["mappedunits"] = line[-1]
		else:
			pass
	return meminfo

def getHDInfo(hdd_name):
	with open("/proc/diskinfo", "r") as hd_file:
		lines = hd_file.readlines()

	for line in lines:
		line = [word.strip() for word in line.split()]
		if line[2] == hdd_name:
			completed_writes = line[7]
			total_milli = line[9]
			return {"writes":complete_writes, "time":total_milli}
	return dict.fromkeys(["writes", "time"])

def getHDWrites(interval, hdd_name):
	dHd = deltaTime(interval, getHDInfo, hdd_name)
	return dHd["writes"]
def getHDWritesPerSecond(interval, hdd_name):
	return getHDWrites()/interval

def getHDWriteTime(interval, hdd_name):
	dHd = deltaTime(interval, getHDInfo, hdd_name)
	return dHd["time"]
	
	

def getPidInfo(pid):
	pidinfo = dict.fromkeys(["name", "sleepavg", "threads"])
	# read in the pid/status file and parse for keywords
	with open("/proc/" + pid + "/status", "r") as pid_file:
		lines = pid_file.readLines()

	for line in lines:
		if line.startswith("Name"):
			pidinfo["name"] = line.split("\t")[-1].strip()
		elif line.startswith("SleepAVG"):
			pidinfo["sleepavg"] = line.split("\t")[-1].strip()[:-1]
		elif line.startswith("Threads"):
			pidinfo["threads"] = line.split("\t")[-1].strip()
		else:
			pass
	return pidinfo

def getPidDict():
	# a regular expression to open all status files in all dirs  in /proc that start with a number
	pids = {}
	pat = re.compile("\d")
	files = os.listdir("/proc")
	files = filter(pat.search, files)
	for pid in files:
		pids[pid] = getPidInfo(pid)
	return pids


class Proc(object):
	"""A Higher level interface and object for /proc"""

	def __init__(self, interval, net_dev, hdd):
		self.interval = interval
		self.net_dev = net_dev
		self.hdd = hdd
		self.getStatTimes = getStatTimes
		self.getCPUPercent = functools.partial(getCPUPercent, self.interval)
		self.getNetInfoOnDev = functools.partial(getNetInfoOnDev, self.net_dev) 
		self.getBytes = functools.partial(getBytes, self.interval, self.net_dev)
		self.getBytesPerSecond = self.getThroughput = functools.partial(getThroughput, self.interval, self.net_dev)
		self.getPackets = functools.partial(getPackets, self.interval, self.net_dev)
		sefl.getPacketsPerSecond = functools.partial(getPacketsPerSecond, self.interval)
		self.getMemInfo = getMemInfo
		self.getHDInfo = functools.partial(getHDInfo, self.hdd)
		self.getHDWrites = functools.partial(getHDWrites, interval, self.hdd)
		self.getHDWritesPerSecond = functools.partial(getHDWritesPerSecond, interval, self.hdd)
		self.getHDWriteTime = functools.partial(getHDWriteTime, interval, self.hdd)

	def tempCall(self, meth, **kwargs):
		pass


if __name__ == "__main__"  :
	TIMEFORMAT = "%y-%m/%d %H:%M:%S"
	INTERVAL = 2
	while True	:
		cpuPct = getCPUPercent(INTERVAL)
		timeStamp = time.strftime(TIMEFORMAT)
		print timeStamp + "\t" + str('%.4f' %cpuPct)


