import os.path as path
from CIP.logic.SlicerUtil import SlicerUtil

class Colors(object):
    __chest_regions__ = None
    __chest_types__ = None

    @staticmethod
    def ChestRegions ():
        """ Get a dict of regions with tuples of (Name, R, G, B) with values between 0 and 255
        @return:
        """
        if Colors.__chest_regions__ is None:
            # Colors.__chest_regions__ = Colors.__readColorMapFile__("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_/CIP/ui/Resources/chest_region_colors.ctbl")
            Colors.__chest_regions__ = Colors.__readColorMapFile__(path.join
                                        (SlicerUtil.CIP_RESOURCES_DIR, "chest_region_colors.ctbl"))
        return Colors.__chest_regions__

    @staticmethod
    def ChestTypes ():
        """ Get a dict of types with tuples of (Name, R, G, B) with values between 0 and 255
        @return:
        """
        if Colors.__chest_types__ is None:
            #Colors.__chest_types__ = Colors.__readColorMapFile__("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_/CIP/ui/Resources/chest_type_colors.ctbl")
            Colors.__chest_types__  = Colors.__readColorMapFile__(path.join
                                        (SlicerUtil.CIP_RESOURCES_DIR, "chest_type_colors.ctbl"))
        return Colors.__chest_types__

    @staticmethod
    def __readColorMapFile__(f):
        d = {}
        for line in open(f, "r+b"):
            ll = line.split(" ")
            d[int(ll[0])] = (ll[1], int(ll[2]), int(ll[3]), int(ll[4]))
        return d