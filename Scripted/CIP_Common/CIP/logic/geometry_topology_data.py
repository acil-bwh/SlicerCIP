'''
Classes that represent a collection of points/structures that will define a labelmap or similar for image analysis purposes.
Currently the parent object is GeometryTopologyData, that can contain objects of type Point and/or BoundingBox.
The structure of the object is defined in the GeometryTopologyData.xsd schema.
Created on Apr 6, 2015

@author: Jorge Onieva
'''

import xml.etree.ElementTree as ET

class GeometryTopologyData:
    # Coordinate System Constants
    UNKNOWN = 0
    IJK = 1
    RAS = 2
    LPS = 3

    __numDimensions__ = 0
    @property
    def numDimensions(self):
        if self.__numDimensions__ == 0:
            # Try to get the number of dimensions from the first point or bounding box
            if len(self.points) > 0:
                self.__numDimensions__ = len(self.points[0].coordinate)
            elif len(self.boundingBoxes) > 0:
                self.__numDimensions__ = len(self.boundingBoxes[0].start)
        return self.__numDimensions__    
    @numDimensions.setter
    def numDimensions(self, value):
        self.__numDimensions__ = value


    __LPStoIJKTransformationMatrix__ = None


    def __init__(self):
        self.__numDimensions__ = 0
        self.coordinateSystem = self.UNKNOWN

        self.points = []
        self.boundingBoxes = []
    
    def addPoint(self, point):
        """Add a new Point from a vector of float coordinates"""
        self.points.append(point)
    
    def addBoundingBox(self, boundingBox):
        self.boundingBoxes.append(boundingBox)
    
    def toXml(self):
        """Generate the XML string representation of this object.
        It doesn't use any special module to keep compatibility with Slicer"""
        output = '<?xml version="1.0" encoding="utf8"?><GeometryTopologyData>'
        if self.numDimensions != 0: 
            output = output +  ('<numDimensions>%i</numDimensions>' % self.numDimensions)

        output = output +  ('<coordinateSystem>%s</coordinateSystem>' % self.coordinateSystemToStr(self.coordinateSystem))
        
        # Concatenate points
        points = "".join(map(lambda i:i.toXml(), self.points))
        # Concatenate bounding boxes
        boundingBoxes = "".join(map(lambda i:i.toXml(), self.boundingBoxes))
        
        return output + points + boundingBoxes + "</GeometryTopologyData>"
   
    @staticmethod
    def fromXml(xml):
        """Build a GeometryTopologyData object from a xml string.
        All the coordinates will be float.
        remark: It uses the ElementTree instead of lxml module to be compatible with Slicer
        """
        root = ET.fromstring(xml)

        geometryTopology = GeometryTopologyData()

        # NumDimensions
        nd = root.find("numDimensions")
        if nd is not None:
            geometryTopology.__numDimensions__ = int(nd.text)

        # Coordinate System
        c = root.find("coordinateSystem")
        if c is not None:
            geometryTopology.coordinateSystem = geometryTopology.coordinateSystemFromStr(c)

        # Points
        for point in root.findall("Point"):
            coordinates = []
            for coord in point.findall("Coordinate/value"):
                coordinates.append(float(coord.text))
            chestRegion = int(point.find("ChestRegion").text)
            chestType = int(point.find("ChestType").text)
            
            # Description
            desc = point.find("Description")
            if desc is not None:
                desc = desc.text
                
            geometryTopology.addPoint(Point(coordinates, chestRegion, chestType, description=desc))

        # BoundingBoxes
        for bb in root.findall("BoundingBox"):
            coordinatesStart = []
            for coord in bb.findall("Start/value"):
                coordinatesStart.append(float(coord.text))
            coordinatesSize = []
            for coord in bb.findall("Size/value"):
                coordinatesSize.append(float(coord.text))
            chestRegion = int(bb.find("ChestRegion").text)
            chestType = int(bb.find("ChestType").text)
            
            # Description
            desc = bb.find("Description")
            if desc is not None:
                desc = desc.text
                            
            geometryTopology.addBoundingBox(BoundingBox(coordinatesStart, coordinatesSize, chestRegion, chestType, description=desc))

        return geometryTopology

    @staticmethod
    def coordinateSystemFromStr(valueStr):
        if valueStr:
            if valueStr == "IJK": return GeometryTopologyData.IJK
            elif valueStr == "RAS": return GeometryTopologyData.RAS
            elif valueStr == "LPS": return GeometryTopologyData.LPS
            else: return GeometryTopologyData.UNKNOWN
        else:
            return GeometryTopologyData.UNKNOWN

    @staticmethod
    def coordinateSystemToStr(valueInt):
        if valueInt == GeometryTopologyData.IJK: return "IJK"
        elif valueInt == GeometryTopologyData.RAS: return "RAS"
        elif valueInt == GeometryTopologyData.LPS: return "LPS"
        return "UNKNOWN"


class Point:
    def __init__(self, coordinate, chestRegion, chestType, description=None, format="%f"):
        """
        :param coordinate: Vector of numeric coordinates
        :param chestRegion: chestRegion Id
        :param chestType: chestType Id
        :param description: optional description of the content the element
        :param format: Default format to print the xml output coordinate values (also acceptable: %i for integers or customized)
        :return:
        """
        self.coordinate = coordinate
        self.chestRegion = chestRegion
        self.chestType = chestType
        self.description = description
        self.format = format
    
    def toXml(self):
        coords = self.toXmlVector(self.coordinate)
        descriptionStr = ''
        if not self.description is None:
            descriptionStr = '<Description>%s</Description>' % self.description
            
        return '<Point><ChestRegion>%i</ChestRegion><ChestType>%i</ChestType>%s<Coordinate>%s</Coordinate></Point>' % \
            (self.chestRegion, self.chestType, descriptionStr, coords)
            
    def toXmlVector(self, array):
        output = ''
        for i in array:
            output = ("%s<value>" + self.format + "</value>") % (output, i) 
        return output

class BoundingBox:
    def __init__(self, start, size, chestRegion, chestType, description=None, format="%f"):
        """
        :param start: vector of coordinates for the starting point of the Bounding Box
        :param size: vector that contains the size of the bounding box
        :param chestRegion: chestRegion Id
        :param chestType: chestType Id
        :param description: optional description of the content the element
        :param format: Default format to print the xml output coordinate values (also acceptable: %i for integers or customized)
        :return:
        """
        self.start = start
        self.size = size
        self.chestRegion = chestRegion
        self.chestType = chestType
        self.description = description
        self.format = format       # Default format to print the xml output coordinate values (also acceptable: %i or customized)

    
    def toXml(self):
        startStr = self.toXmlVector(self.start)
        sizeStr = self.toXmlVector(self.size)
        descriptionStr = ''
        if not self.description is None:
            descriptionStr = '<Description>%s</Description>' % self.description
        return '<BoundingBox><ChestRegion>%i</ChestRegion><ChestType>%i</ChestType>%s<Start>%s</Start><Size>%s</Size></BoundingBox>' % \
            (self.chestRegion, self.chestType, descriptionStr, startStr, sizeStr)
            

    def toXmlVector(self, array):
        output = ''
        for i in array:
            output = ("%s<value>" + self.format + "</value>") % (output, i)
        return output

