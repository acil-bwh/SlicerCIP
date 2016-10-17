from collections import OrderedDict


class BodyCompositionParameters(object):
    INF = 100000
    MAX_REGION_TYPE_CODE = 65536  # 11111111 11111111

    """ Allowed region types"""
    regionTypes = OrderedDict()
    regionTypes["UNDEFINED"] = (0, "Undefined region")
    regionTypes["LEFT"] = (23, "Left")
    regionTypes["RIGHT"] = (24, "Right")
    regionTypes["ABDOMEN"] = (27, "Abdomen")
    regionTypes["LIVER"] = (25, "Liver")
    regionTypes["PARAVERTEBRAL"] = (28, "Paravertebral")
    regionTypes["SPLEEN"] = (26, "Spleen")
    regionTypes["SKELETON"] = (31, "Skeleton")

    """Allowed tissue types"""
    chestTypes = OrderedDict()
    chestTypes["UNDEFINEDTYPE"] = (0, "Undefined type")
    chestTypes["MUSCLE"] = (80, "Muscle")
    chestTypes["PECTORALISMAJOR"] = (53, "Pectoralis Major")
    chestTypes["PECTORALISMINOR"] = (52, "Pectoralis Minor")
    chestTypes["SUBCUTANEOUSFAT"] = (70, "Subcutaneous fat")
    chestTypes["VISCERALFAT"] = (71, "Visceral fat")

    """Allowed combinations.
    IMPORTANT: the colors are just kept like legacy code and are not actually used.
    To view/change the current colors go to BodyCompositionColorMap.ctbl file in Resources folder
      Structure of the object:
      - RegionId
      - TypeId
      - Red level (0-1)      DEPRECATED
      - Green level (0-1)    DEPRECATED
      - Blue level (0-1)     DEPRECATED
      - Threshold Min
      - Threshold Max
      - Window Width
      - Window level
      - Preprocessing"""
    REGION_ID = 0  # Chest Region (0-255)
    TYPE_ID = 1  # Chest Type (0-255)
    RED = 2  # Red level (0-1)      DEPRECATED
    GREEN = 3  # Green level (0-1)    DEPRECATED
    BLUE = 4  # Blue level (0-1)     DEPRECATED
    THRESHOLD_MIN = 5  # Threshold (minimum) for the label. User cannot paint any region with this label if the gray intensity for that zone is below this limit.  (-INF => no threshold)
    THRESHOLD_MAX = 6  # Threshold (maximum) for the label. User cannot paint any region with this label if the gray intensity for that zone is beneath this limit.  (INF => no threshold)
    WINDOW_WIDTH = 7  # Width of the preferred contrast window to segment this label
    WINDOW_LEVEL = 8  # Level of the preferred contrast window to segment this label (the whole window is [Level-Window/2, Level+Window/2]
    PREPROCESSING = 9  # This tissue should have a preprocessing before calculating the analysis (ex: muscle). Numeric value indicating the type of processing (0=no preprocessing, 1=closing)
    DEFAULT_TOOL = 10  # Default Tool Effect (ex: PaintEffect, RectangleEffect, etc.)
    DEFAULT_RADIUS = 11  # Default radius for the PaintEffect

    allowedCombinations = \
        (("UNDEFINED", "UNDEFINEDTYPE", 0, 0, 0, -INF, INF, -INF, INF, 0, "PaintEffect", 8),
         ("ABDOMEN", "VISCERALFAT", 0.1, 0.39, 0.79, -250, 50, 1300, -550, 0, "PaintEffect", 8),
         ("PARAVERTEBRAL", "MUSCLE", 0.95, 0.23, 0.10, -50, 90, 140, 20, 1, "PaintEffect", 8),
         ("RIGHT", "SUBCUTANEOUSFAT", 0.68, 0.86, 0.9, -200, 0, 1300, -550, 0, "RectangleEffect", 8),
         ("LEFT", "PECTORALISMAJOR", 0.74, 0.1, 0.1, -50, 90, 140, 20, 1, "PaintEffect", 8),
         ("PARAVERTEBRAL", "SUBCUTANEOUSFAT", 0.80, 0.58, 0.11, -200, 0, 1300, -550, 0, "RectangleEffect", 8),
         ("LEFT", "PECTORALISMINOR", 0.75, 0.34, 0.34, -50, 90, 140, 20, 1, "PaintEffect", 5),
         ("RIGHT", "PECTORALISMAJOR", 0.64, 0, 0, -50, 90, 140, 20, 1, "PaintEffect", 8),
         ("RIGHT", "PECTORALISMINOR", 0.65, 0.24, 0.24, -50, 90, 140, 20, 1, "PaintEffect", 5),
         ("LEFT", "SUBCUTANEOUSFAT", 0.78, 0.96, 1, -200, 0, 1300, -550, 1, "RectangleEffect", 8),
         ("LIVER", "UNDEFINEDTYPE", 0.79, 0.87, 0.06, -INF, INF, 140, 20, 0, "PaintEffect", 8),
         ("SPLEEN", "UNDEFINEDTYPE", 0.61, 0.42, 0.64, -INF, INF, 140, 20, 0, "PaintEffect", 8),
         ("SKELETON", "MUSCLE", 0, 0, 0, -29, 150, 179, 61, 0, "PaintEffect", 8))

    def __init__(self):
        self.loadParameters()

    def loadParameters(self):
        """Load the allowed ChestRegion-ChestTypes and builds the main structure of parameters"""

        """ "Lists of lists" where each item contains the next data:
        - LabelMap code id (result of mixing chest region and chest type)
        - Region string key
        - Type string key
        - Red (double 0-1)
        - Green (double 0-1)
        - Blue (double 0-1)
        - Threshold min
        - Threshold max
        - Window_width
        - Window_level """
        self.allowedCombinationsParameters = list()

        for item in self.allowedCombinations:
            newCombination = list()
            # Add the labelmap code for this combination and then the rest of the parameters
            newCombination.append(self.getValueFromChestRegionAndTypeLabels(item[self.REGION_ID], item[self.TYPE_ID]))
            for component in item:
                # Add Region, Type,Color, etc.
                newCombination.append(component)

            # Add the new element to the collection
            self.allowedCombinationsParameters.append(newCombination)

    def getItem(self, region, type):
        """Return the allowed combination parameters (or Nothing if the combination is not valid)"""
        for item in self.allowedCombinationsParameters:
            if self.getRegionStringCodeItem(item) == region and self.getTypeStringCodeItem(item) == type:
                return item
        return None

    def getValueFromChestRegionAndTypeLabels(self, region, type):
        """Get the value for the label map for the current chest region and type"""
        # Get the numeric codes from the region and types string codes
        region = self.regionTypes[region][0]
        type = self.chestTypes[type][0]

        type = (type << 8)  # Type is the most significant byte
        combinedValue = region + type
        return combinedValue

    def getIntCodeItem(self, item):
        """Get the integer code for this combination in an item from the mainParameters structure"""
        return item[0]

    def getRegionStringCodeItem(self, item):
        """Get the region string code in an item from the mainParameters structure"""
        return item[self.REGION_ID + 1]  # The first item is the label map code

    def getRegionStringDescriptionItem(self, item):
        """Return the label description for a region in an allowed combination"""
        code = self.getRegionStringCodeItem(item)
        return self.regionTypes[code][1]

    def getTypeStringCodeItem(self, item):
        """Get the type label code in an item from the mainParameters structure"""
        return item[self.TYPE_ID + 1]  # The first item is the label map code

    def getTypeStringDescriptionItem(self, item):
        """Return the label description for a type in an allowed combination"""
        code = self.getTypeStringCodeItem(item)
        return self.chestTypes[code][1]

    def getFullStringDescriptionItem(self, item):
        """Return the label "region-type" in an allowed combination or just region if type is undefined"""
        region = self.getRegionStringDescriptionItem(item)
        typeId = self.getTypeStringCodeItem(item)

        if typeId == "UNDEFINEDTYPE":
            return region
        return "{0}-{1}".format(region, self.getTypeStringDescriptionItem(item))

    def getRedItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return item[self.RED + 1]  # The first item is the label map code

    def getGreenItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return item[self.GREEN + 1]  # The first item is the label map code

    def getBlueItem(self, item):
        """Get the Red value in an item from the mainParameters structure"""
        return item[self.BLUE + 1]  # The first item is the label map code

    def getThresholdRange(self, item):
        """Returns a tuple (MIN, MAX) with the threshold range for the selected combination"""
        return (item[self.THRESHOLD_MIN + 1], item[self.THRESHOLD_MAX + 1])

    def getWindowRange(self, item):
        """Returns a tuple (Window_size, Window_center_level) with the window range for the selected combination"""
        width = item[self.WINDOW_WIDTH + 1]
        level = item[self.WINDOW_LEVEL + 1]
        if width == self.INF or level == self.INF:
            return None

        return (width, level)

    def getPreprocessingType(self, item):
        return item[self.PREPROCESSING + 1]

    def getDefaultTool(self, item):
        return item[self.DEFAULT_TOOL + 1]

    def getDefaultRadius(self, item):
        return item[self.DEFAULT_RADIUS + 1]
