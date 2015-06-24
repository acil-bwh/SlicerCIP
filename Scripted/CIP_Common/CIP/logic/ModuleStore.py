import os

from __main__ import slicer


from . import SlicerUtil

class ModuleStore(object):
    def __init__(self, moduleName):
        self.__moduleName__ = moduleName
        self.__settingsPath__ = os.path.join(SlicerUtil.getModuleFolder(moduleName), "Resources", moduleName + "_storage.csv")
        print(self.__settingsPath__)


