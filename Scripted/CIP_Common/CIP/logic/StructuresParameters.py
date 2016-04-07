from collections import OrderedDict
from CIP.logic.SlicerUtil import SlicerUtil
import xml.etree.ElementTree as et
import colorsys
from CIP.logic.Colors import Colors

class StructuresParameters(object):
    INF = 100000

    """
        Ids:
        - StructureId
        - ChestRegion
        - ChestType
        - Red level (0-1)
        - Green level (0-1)
        - Blue level (0-1)
        - WindowWidth
        - WindowLevel
        - Plane
        """
    STRUCTURE_ID = 0                        # Structure (0-255)
    CHEST_REGION_ID = 1                     # ChestRegion id to which the structure is linked
    CHEST_TYPE_ID = 2                       # ChestType id to which the structure is linked
    DESCRIPTION = 3                         # Description
    RED = 4                                 # Red level (0-1). DEPRECATED
    GREEN = 5                               # Green level (0-1). DEPRECATED
    BLUE = 6                                # Blue level (0-1). DEPRECATED
    WINDOW_WIDTH = 7                        # Width of the preferred contrast window to segment this label
    WINDOW_LEVEL = 8                        # Level of the preferred contrast window to segment this label (the whole window is [Level-Window/2, Level+Window/2]
    PLANE = 9                               # A=Axial, S=Sagital, C=Coronal


    """Structures"""
    structureTypes = OrderedDict()
    # structureTypes["UNDEFINED"] = (0, 0, 0, "Undefined structure", 0, 0, 0, -INF, INF , '')
    #
    # # IMPORTANT: these colors are not valid anymore. To change the colors of the structures you will have to update the file "StructuresColorMap.ctbl" in ui resources
    #
    # #Axial Slice
    # slicePlane="Axial"
    # structureTypes['LeftHumerus'+slicePlane] = (1, 34, 0, 'Left Humerus (Axial)', 0.75, 0.05, 0, 900, 50, 'A')
    # structureTypes['RightHumerus'+slicePlane] = (2, 35, 0, 'Right Humerus (Axial)', 0.95, 0.23, 0.10, 900, 50, 'A')
    # structureTypes['LeftScapula'+slicePlane] = (3, 37, 0, 'Left Scapula (Axial)', 0.48, 0.66, 0.7, 900, 50, 'A')
    # structureTypes['RightScapula'+slicePlane] = (4, 38, 0, 'Right Scapula (Axial)', 0.68, 0.86,    0.9, 900, 50, 'A')
    # structureTypes['LeftPectoralis'+slicePlane] = (5, 56, 0, 'Left Pectoralis (Axial)', 0.65, 0.24, 0.24, 900, 50, 'A')
    # structureTypes['RightPectoralis'+slicePlane] = (6, 57, 0, 'Right Pectoralis (Axial)', 0.85, 0.44, 0.44, 900, 50, 'A')
    # structureTypes['TransversalAorta'+slicePlane] = (7, 46, 0, 'Transversal Aorta (Axial)', 0.05, 0.8, 0.2, 900,    50, 'A')
    # structureTypes['PulmonaryArtery'+slicePlane] = (8, 18, 0, 'Pulmonary Artery (Axial)', 0.1, 0.2, 0.7, 900, 50, 'A')
    # structureTypes['LeftCoronoraryArtery'+slicePlane] = (9, 50, 0, 'Left Coronorary Artery (Axial)', 0.2, 0.3, 0.1, 900, 50, 'A')
    # structureTypes['WholeHeart'+slicePlane] = (10, 16, 0, 'Whole Heart (Axial)', 0.9, 0.75, 0.1, 900, 50, 'A')
    # structureTypes['Liver'+slicePlane] = (11, 25, 0, 'Liver (Axial)', 0, 0.5, 0.5, 900, 50, 'A')
    # structureTypes['Spleen'+slicePlane] = (12, 26, 0, 'Spleen (Axial)', 0.4, 0.3, 0.9, 900, 50, 'A')
    # structureTypes['LeftKidney'+slicePlane] = (13, 43, 0, 'Left Kidney (Axial)', 0.05, 0.7, 0.2, 900, 50, 'A')
    # structureTypes['RightKidney'+slicePlane] = (14, 44, 0, 'Right Kidney (Axial)', 0.9, 0.2, 0.4, 900, 50, 'A')
    # structureTypes['Nodule'+slicePlane] = (15, 0, 86, 'Nodule (Axial)', 0.9, 0.2, 0.4, 900, 50, 'A')
    # structureTypes['AscendingAorta'+slicePlane] = (16, 32, 45, 'Ascending Aorta (Axial)', 0.9, 0.2, 0.4, 900, 50, 'A')
    #
    # #Sagittal Slice
    # slicePlane="Sagittal"
    # structureTypes['TransversalAorta'+slicePlane] = (31, 46, 0, 'Transversal Aorta (Sagittal)', 0.3, 0.1, 0.8, 900, 50, 'S')
    # structureTypes['AscendingAorta'+slicePlane] = (32, 45, 0, 'Ascending Aorta (Sagittal)', 0.8, 0.8, 0, 900, 50, 'S')
    # structureTypes['PulmonaryArtery'+slicePlane] = (33, 18, 0, 'Pulmonary Artery (Sagittal)', 0.2, 0.32, 0.1, 900, 50, 'S')
    # structureTypes['WholeHeart'+slicePlane] = (34, 16, 0, 'Whole Heart (Sagittal)', 0.1, 0.3, 0.57, 900, 50, 'S')
    # structureTypes['Sternum'+slicePlane] = (35, 32, 0, 'Sternum (Sagittal)', 0.4, 0.2, 0.2, 900, 50, 'S')
    # structureTypes['Trachea2'+slicePlane] = (36, 58, 0, 'Trachea (Sagittal)', 0.1, 0.5, 0.9, 900, 50, 'S')
    # structureTypes['Spine'+slicePlane] = (37, 51, 0, 'Spine (Sagittal)', 0.2, 0.8, 0.8, 900, 50, 'S')
    # structureTypes['Liver'+slicePlane] = (38, 25, 0, 'Liver (Sagittal)', 0, 1, 1, 900, 50, 'S')
    # structureTypes['LeftHilum'+slicePlane] = (39, 40, 0, 'Left Hilum (Sagittal)', 0.7, 0.3, 0.6, 900, 50, 'S')
    # structureTypes['RightHilum'+slicePlane] = (40, 41, 0, 'Right Hilum (Sagittal)', 0.5, 0.1, 0.4, 900, 50, 'S')
    # structureTypes['LeftVentricle'+slicePlane] = (41, 52, 0, 'Left Ventricle (Sagittal)', 0.2, 0.1, 0.3, 900, 50, 'S')
    # structureTypes['Nodule'+slicePlane] = (42, 0, 86, 'Nodule (Sagittal)', 0.9, 0.2, 0.4, 900, 50, 'S')
    #
    # # Coronal Slice
    # slicePlane="Coronal"
    # structureTypes['DescendingAorta'+slicePlane] = (51, 47, 0, 'Descending Aorta (Coronal)', 0.4, 0.2, 0.9, 900, 50, 'C')
    # structureTypes['Trachea2'+slicePlane] = (52, 58, 0, 'Trachea (Coronal)', 0.9, 0.4, 0.4, 900, 50, 'C')
    # structureTypes['AscendingAorta'+slicePlane] = (53, 45, 0, 'Ascending Aorta (Coronal)', 0.9, 0.9, 0.1, 900, 50, 'C')
    # structureTypes['Liver'+slicePlane] = (54, 25, 0, 'Liver (Coronal)', 0.1, 0.15, 0.15, 900, 50, 'C')
    # structureTypes['LeftVentricle'+slicePlane] = (55, 52, 0, 'Left Ventricle (Coronal)', 0.1, 0.2, 0.6, 900, 50, 'C')
    # structureTypes['LeftDiaphragm'+slicePlane] = (56, 64, 0, 'Left Diaphragm (Coronal)', 0.1, 0.8, 0.4, 900, 50, 'C')
    # structureTypes['LeftChestWall'+slicePlane] = (57, 62, 0, 'Left Chest Wall (Coronal)', 0.8, 0.3, 0.3, 900, 50, 'C')
    # structureTypes['RightChestWall'+slicePlane] = (58, 63, 0, 'Right Chest Wall (Coronal)', 0.6, 0.1, 0.1, 900, 50, 'C')
    # structureTypes['LeftSubclavian'+slicePlane] = (59, 48, 0, 'Left Subclavian Artery (Coronal)', 0.6, 0.7, 0.3, 900, 50, 'C')
    # structureTypes['Spine'+slicePlane] = (60, 51, 0, 'Spine (Coronal)', 0.2, 0.7, 0.2, 900, 50, 'C')
    # structureTypes['HernialHiatus'+slicePlane] = (61, 66, 81, 'Hernial Hiatus (Coronal)', 0.2, 0.5, 0.5, 900, 50, 'C')
    # structureTypes['PulmonaryArtery'+slicePlane] = (62, 8, 18, 'Pulmonary Artery (Coronal)', 0, 0, 0, 900, 50, 'C')
    # structureTypes['Nodule'+slicePlane] = (63, 0, 86, 'Nodule (Coronal)', 0.9, 0.2, 0.4, 900, 50, 'C')

    def getItem(self, structureId):
        return self.structureTypes[structureId]

    def getIntCodeItem(self, structureId):
        """Get the integer code (ID)"""
        return self.getItem(structureId)[self.STRUCTURE_ID]
    
    def getRegionIdItem(self, structureId):
        """Get the Region id to which this structure is linked"""
        return self.getItem(structureId)[self.CHEST_REGION_ID]
    
    def getTypeIdItem(self, structureId):
        """Get the Region id to which this structure is linked"""
        return self.getItem(structureId)[self.CHEST_TYPE_ID]

    def getDescriptionItem(self, structureId):
        """Return the full description label"""
        return self.getItem(structureId)[self.DESCRIPTION]

    def getRedItem(self, structureId):
        """Get the Red value in an item from the mainParameters structure"""
        return self.getItem(structureId)[self.RED]

    def getGreenItem(self, structureId):
        """Get the Red value in an item from the mainParameters structure"""
        return self.getItem(structureId)[self.GREEN]

    def getBlueItem(self, structureId):
        """Get the Red value in an item from the mainParameters structure"""
        return self.getItem(structureId)[self.BLUE]

    def getWindowRange(self, structureId):
        """Returns a tuple (Window_size, Window_center_level) with the window range for the selected combination"""
        item = self.getItem(structureId)
        if not item:
            return None     # Item not found

        width = item[self.WINDOW_WIDTH]
        level = item[self.WINDOW_LEVEL]
        if width == self.INF or level == self.INF:
            return None

        return (width, level)

    def getPlaneItem(self, structureId):
        return self.getItem(structureId)[self.PLANE]

    def readStructuresFromFile(self, xmlFilePath, colorPriorityForRegions=True):
        """ Read all the structure types from a XML file
        @param xmlFilePath: path to the xml file
        @param colorPriorityForRegions: when True, the primary color for the structure
        will be the ChestRegion. The different ChestTypes will be calculated playing with saturation
        depending on how many different types we have for a region.
        When False, the behaviour will be the opposite
        """
        with open(xmlFilePath, 'r+b') as f:
            xml = f.read()
        root = et.fromstring(xml)
        # At the moment just replicate the previous structure for compatibility purposes
        # In the general case, we should create a "dictionary of dictionaries" with one entry per structure
        self.structureTypes = OrderedDict()
        for structure in root.findall("Structure"):
            l = [None]*10
            #structureTypes['DescendingAorta'+slicePlane] = (0.4, 0.2, 0.9, 900, 50, 'C')
            l[self.STRUCTURE_ID] = int(structure.find("Id").text)
            l[self.CHEST_REGION_ID] = int(structure.find("ChestRegion").text)
            l[self.CHEST_TYPE_ID] = int(structure.find("ChestType").text)
            l[self.DESCRIPTION] = structure.find("Description").text
            l[self.RED] = None
            l[self.GREEN] = None
            l[self.BLUE] = None
            l[self.WINDOW_LEVEL] = int(structure.find("WindowLevel").text)
            l[self.WINDOW_WIDTH] = int(structure.find("WindowWidth").text)
            l[self.PLANE] = structure.find("Plane").text
            code = structure.find("CodeLabel").text
            self.structureTypes[code] = l
            # print("Structure created: ", self.structureTypes[code])

        if colorPriorityForRegions:
            primaryKey = self.CHEST_REGION_ID
            secondaryKey = self.CHEST_TYPE_ID
            primaryColorList = Colors.ChestRegions()
            secondaryColorList = Colors.ChestTypes()
        else:
            primaryKey = self.CHEST_TYPE_ID
            secondaryKey = self.CHEST_REGION_ID
            primaryColorList = Colors.ChestTypes()
            secondaryColorList = Colors.ChestRegions()
        primaryList = {}
        # Count all the different types for every region (or viceversa)
        for structure in self.structureTypes.itervalues():
            # Get the ChestRegion (or ChestType)
            st = structure[primaryKey]
            if st == 0:
                # Undefined primary key. Try to do the process with the secondary list.
                # Ex: ChestRegions is the primary list but we have also several ChestTypes with undefined ChestRegion.
                # In this case, we would take the ChestType color as the color reference
                st = structure[secondaryKey]

            if primaryList.has_key(st):
                primaryList[st][0] += 1
            else:
                primaryList[st] = [1, 0]

        # Get step for every region based on the number of types for this region (or viceversa)
        bottom_hsv = 0.2
        for primaryType in primaryList.itervalues():
            primaryType[1] = (1-bottom_hsv) / primaryType[0]
        # print ("Colors structure created (with step): ", primaryList)
        # print("Primary colors List: ", primaryColorList)
        # print ("****************************")
        # print ("**************************")
        # Fill the colors
        for strKey, structure in self.structureTypes.iteritems():
            key = structure[primaryKey]
            rgbColorPrev = primaryColorList[key]
            # print ("structure[{0}] = {1}".format(key, primaryColorList[key]))
            if key == 0:
                key = structure[secondaryKey]
                rgbColorPrev = secondaryColorList[key]
            # Convert the color to HSV
            hsvColor = colorsys.rgb_to_hsv(rgbColorPrev[1] / 255.0, rgbColorPrev[2] / 255.0, rgbColorPrev[3] / 255.0)

            # Convert hsv to rgb after modifying the saturation
            hsvColorModified = (hsvColor[0], primaryList[key][0] * primaryList[key][1] + bottom_hsv, hsvColor[1])
            rgbColor = colorsys.hsv_to_rgb(hsvColorModified[0], hsvColorModified[1], hsvColorModified[2])
            # print ("Key: {0}; Prev rgbColor: {1}; Prev hsvColor: {2}; Current rgb: {3}: Current hsv: {4}".
            #        format(key, rgbColorPrev, hsvColor, rgbColor, hsvColorModified))

            primaryList[key][0] -= 1
            # print("Primary list modified. ", primaryList)
            # Assign the color
            structure[self.RED] = int(rgbColor[0] * 255)
            structure[self.GREEN] = int(rgbColor[1] * 255)
            structure[self.BLUE] = int(rgbColor[2] * 255)
            # print ("*********")
            # print("Structures[{0}] = {1}: ".format(strKey, structure))
        # print "Final structures:"
        # print(self.structureTypes)

    def createColormapNode(self, colormapName):
        colorNode = SlicerUtil.createNewColormapNode(colormapName, numberOfColors=len(self.structureTypes))
        for structure in self.structureTypes.itervalues():
            colorNode.AddColor(structure[self.DESCRIPTION], structure[self.RED], structure[self.GREEN], structure[self.BLUE])
        return colorNode

    def generateXml(self):
        """ Generate a xml file from a dict of structures
        @return:
        """
        xml = ""
        xml += '<?xml version="1.0" encoding="utf8"?><Structures>'

        for structure in self.structureTypes:
            xml += "<Structure>"
            xml += "<Id>{0}</Id>".format(self.getIntCodeItem(structure))
            xml += "<CodeLabel>{0}</CodeLabel>".format(structure)
            xml += "<ChestRegion>{0}</ChestRegion>".format(self.getRegionIdItem(structure))
            xml += "<ChestType>{0}</ChestType>".format(self.getTypeIdItem(structure))
            xml += "<Description>{0}</Description>".format(self.getDescriptionItem(structure))
            xml += "<WindowWidth>{0}</WindowWidth>".format(self.getItem(structure)[self.WINDOW_WIDTH])
            xml += "<WindowLevel>{0}</WindowLevel>".format(self.getItem(structure)[self.WINDOW_LEVEL])
            xml += "<Plane>{0}</Plane>".format(self.getPlaneItem(structure))
            xml += "</Structure>"

        xml += "</Structures>"
        return xml

strs = StructuresParameters()
strs.readStructuresFromFile("/Users/jonieva/Projects/ACILSlicer/CIP_StructuresDetection/Resources/structures.xml")