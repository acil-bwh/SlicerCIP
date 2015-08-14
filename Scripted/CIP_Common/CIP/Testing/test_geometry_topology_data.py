from CIP.logic.GeometryTopologyData import *
from lxml import etree
import inspect, os



def test_execute():
    currentDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory

    g = GeometryTopologyData()
    g.numDimensions = 2
    g.coordinateSystem = g.RAS
    g.addPoint(Point([2, 3.5], 2, 5, "My desc", "%f"))
    g.addPoint(Point([2, 3.5], 2, 5, format="%i"))
    g.addBoundingBox(BoundingBox([2, 3.5], [1,1], 2, 5, format="%i"))
    g.addBoundingBox(BoundingBox([2, 3.5], [1,1], 2, 5, format="%f"))
    xml = g.toXml()

    with open(os.path.join(currentDir, "geometryTopologyData-sample.xml"), 'r+b') as f:
        expectedOutput = f.read()
    assert xml == expectedOutput, "XML generated: " + xml

    # Validate schema with lxml
    with open(os.path.abspath(os.path.join(currentDir, "..", "logic", "GeometryTopologyData.xsd")), 'r+b') as f:
        xsd = f.read()
    schema = etree.XMLSchema(etree.XML(xsd))
    xmlparser = etree.XMLParser(schema=schema)
    etree.fromstring(xml, xmlparser)

