""" Simple utility to measure times in a more direct way using time module.

Example of use (in static mode):
GlobalTimer.start()
op1()
print "op1 lasted {} seconds".format(GlobalTimer.lap())
op2()
print "op2 lasted {} seconds".format(GlobalTimer.lap())
op3()
print "The total time was {} seconds".format(GlobalTimer.stop())
# Equivalent:
GlobalTimer.stop()
print "The total time was {} seconds".format(GlobalTimer.total_time())
"""
import time

class Timer(object):
    def __init__(self):
        self.__laps__ = []
        self.start()

    def start(self):
        self.__laps__ = [time.time()]

    def lap(self):
        self.__laps__.append(time.time())
        return self.last_lap()

    def stop(self):
        self.lap()
        return self.total_time()

    def total_time(self):
        if len (self.__laps__) < 2:
            return 0
        return self.__laps__[-1] - self.__laps__[0]

    def last_lap(self):
        if len (self.__laps__) < 2:
            return 0
        return self.__laps__[-1] - self.__laps__[-2]

class GlobalTimer(object):
    __timer__ = Timer()

    @staticmethod
    def start():
        GlobalTimer.__timer__.start()

    @staticmethod
    def lap():
        return GlobalTimer.__timer__.lap()

    @staticmethod
    def stop():
        return GlobalTimer.__timer__.stop()

    @staticmethod
    def total_time():
        return GlobalTimer.__timer__.total_time()

    @staticmethod
    def last_lap():
        return GlobalTimer.__timer__.last_lap()