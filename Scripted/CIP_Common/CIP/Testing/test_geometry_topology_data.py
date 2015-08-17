import os, sys
from lxml import etree
from CIP.logic.geometry_topology_data import *


if len(sys.argv) == 1:
    this_dir = os.path.dirname(os.path.realpath(__file__))     # Directory where this file is contained
    xml_file = os.path.join(this_dir, "geometryTopologyData-sample.xml")
    xsd_file = os.path.abspath(os.path.join(this_dir, "..", "logic", "GeometryTopologyData.xsd"))
else:
    xsd_file = sys.argv[1]
    xml_file = sys.argv[2]


def test_geometry_topology_data_write_read():
    """ Create a GeometryTopology object that must be equal to the one in xml_file.
    It also validates the xml schema against the xsd file
    """
    g = GeometryTopologyData()
    g.numDimensions = 3
    g.coordinateSystem = g.RAS
    g.addPoint(Point([2, 3.5, 3], 2, 5, "My desc", "%f"))
    g.addPoint(Point([2, 3.5, 3], 2, 5, format="%i"))
    g.addBoundingBox(BoundingBox([2, 3.5, 3], [1, 1, 4], 2, 5, format="%i"))
    g.addBoundingBox(BoundingBox([2, 3.5, 3], [1, 1, 3], 2, 5, format="%f"))

    xml = g.toXml()

    # Compare XML output
    with open(xml_file, 'r+b') as f:
        expectedOutput = f.read()
    assert xml == expectedOutput, "XML generated: " + xml

    # Validate schema with lxml
    with open(xsd_file, 'r+b') as f:
        xsd = f.read()
    schema = etree.XMLSchema(etree.XML(xsd))
    xmlparser = etree.XMLParser(schema=schema)
    etree.fromstring(xml, xmlparser)

def test_geometry_topology_data_schema():
    """ Validate the current sample xml file with the current schema
    """
    # Read xml
    with open(xml_file, 'r+b') as f:
        xml = f.read()

    # Validate schema with lxml
    with open(xsd_file, 'r+b') as f:
        xsd = f.read()
    schema = etree.XMLSchema(etree.XML(xsd))
    xmlparser = etree.XMLParser(schema=schema)
    etree.fromstring(xml, xmlparser)


