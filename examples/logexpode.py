#!/usr/bin/env python

#~~~~~~~
"""A utility to explode a log file 'explode.log'"""
#~~~~~~~

from __future__ import with_statement
import random
import time

class LogExploder(object):
    """A utility to simulate explosive logs commonly seen
    when an application enters a unknown/defunct/error state"""

    def __init__(self, log_filename="explode.log"):
        self.log_filename = log_filename
        self.log=None
        super(LogExploder, self).__init__()
    
    def explode(self, low_write=10000, high_write=None, append=False):
        """Explode the log, designated to self.log_filename
        Arguments:
            [low_write] - an int, the lower bound of the explosion. [10000]
            [high_write] - an int, the upper bound of the explosion. [low_write*2]
            [append] - a bool, append the log instead of overwriting [False]
        Returns:
            end_time - a float, the time after the explosion finished"""
        high_write = high_write or low_write*2
        explosive_writes = random.randint(low_write, low_write*2)
        start_time = time.time()
        write_mode = 'w+' if append else 'w'
        print "Exploding %d writes at %10.6f" % (explosive_writes, start_time)
        with open(self.log_filename, write_mode) as self.log:
            for current_write in xrange(explosive_writes):
                current_time = time.time()
                self.log.write("Logging write :: %d :: %10.6f\n" % (current_write, current_time))
                self.log.flush()
        end_time = time.time()
        # Clean up and Report
        self.log = None
        print "Total explosion time:", end_time - start_time
        print "Exiting with log set to:", self.log
        return end_time

    def multi_explode(self, explosions=5, rest_interval=.1, low_write=10000, high_write=None):
        """Explode the file multiple times, optionally resting in between
        Arguments:
            [explosions] - an int, the number of total explosions to launch. [5]
            [rest_interval] - a float/int, the number of seconds to rest in between explosions [.1]
            [low_write] - an int, the lower bound of the explosions. [10000]
            [high_write] - an int, the upper bound of the explosions. [low_write*2]
        Returns:
            end_time - a float, the time after the last explosion finishes"""
        end_time = None
        for explosion in xrange(explosions):
            print "Explosion:", explosion
            end_time = self.explode(low_write, high_write, True)
            time.sleep(rest_interval)
        return end_time
    
    def write_and_explode(self, normal_write_interval=1, max_normal_writes=60, low_write=10000, high_write=None):
        """Write normally to a file, and then explode.
        Arguments:
            [normal_write_interval] - a float/int, the number of seconds to rest in between explosions [1]
            [max_normal_writes] - an int, the upper bound of normal writes.  Must be higher than 20. [60]
            [low_write] - an int, the lower bound of the explosions. [10000]
            [high_write] - an int, the upper bound of the explosions. [low_write*2]
        Returns:
            end_time - a float, the time after the last explosion finishes"""
        # Make sure we have a maximum number of writes 20 or higher
        min_normal_writes = 20
        if max_normal_writes < 20:
            max_normal_writes = 20
        total_writes = random.randint(min_normal_writes, max_normal_writes)
        start_time = time.time()
        print "Writing %d normal writes at %10.6f" % (total_writes, start_time)
        with open(self.log_filename, 'w') as self.log:
            for current_write in xrange(total_writes):
                current_time = time.time()
                self.log.write("Logging write :: %d :: %10.6f\n" % (current_write, current_time))
                self.log.flush()
                time.sleep(normal_write_interval)
        self.log = None
        end_time = self.explode(low_write, high_write, True)
        return end_time


class ExplodeLogDict(dict, object):

    def __init__(self, log_filename='explode.log'):
        with open(log_filename) as log:
            lines = log.readlines()
            strip = lambda x: (x.strip())
            for line in lines:
                write_number,time_stamp = map(strip, line.split("::")[1:])
                self[int(write_number)] = float(time_stamp)
        super(ExplodeLogDict, self).__init__()



if __name__ == "__main__":
    exploder = LogExploder()
    exploder.explode()
    exploder.multi_explode(explosions=2)
    log_dict = ExplodeLogDict()
    print "write 2:", log_dict[2]

