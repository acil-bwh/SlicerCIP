""" Update a list of xml files because of changes in the xml format (among others)
"""
import sys, os
import os.path as path

sys.path.append("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/")
from CIP.logic import geometry_topology_data as gtd
from CIP.logic import Util

#files_dir = sys.argv[1]
files_dir = "/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_ParenchymaSubtypeTraining/Results"
results_dir = path.join(files_dir, "Results")
if not path.isdir(results_dir):
    # Create the results folder if it doesn't exist
    os.makedirs(results_dir)
files = os.listdir(files_dir)

types_replace = {
    # TODO: use the right type substitution
    84: 94,
}

for file_name in files:
    if Util.get_file_extension(file_name) != ".xml":
        continue
    p = path.join(files_dir, file_name)
    print ("Processing {0}...".format(file_name))
    with open(p, "r+b") as f:
        xml = f.read()
        geom = gtd.GeometryTopologyData.from_xml(xml)
        geom.num_dimensions = 3
        for point in geom.points:
            if types_replace.has_key(point.chest_type):
                # Replace type
                point.chest_type = types_replace[point.chest_type]
            if geom.coordinate_system != geom.LPS:
                geom.coordinate_system = geom.LPS
                # Switch to LPS (RAS will be assumed)
                point.coordinate = Util.switch_ras_lps(point.coordinate)
    # Save file
    xml = geom.to_xml()
    p = path.join(results_dir, file_name)
    with open(p, "w") as f:
        f.write(xml)