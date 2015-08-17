
ADD_TEST( NAME test_geometry_topology_data COMMAND nosetests
  ${CMAKE_SOURCE_DIR}/Scripted/CIP_Common/CIP/Testing/test_geometry_topology_data.py
  /Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/CIP/logic/GeometryTopologyData.xsd
  /Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/CIP/Testing/geometryTopologyData-sample.xml)