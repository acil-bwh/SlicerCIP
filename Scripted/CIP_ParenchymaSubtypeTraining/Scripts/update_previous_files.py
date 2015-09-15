""" Update a list of xml files because of changes in the xml format and redefinition of types agreed on 2015-09-08
"""
import sys, os
import os.path as path

sys.path.append("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/")
from CIP.logic import geometry_topology_data as gtd
from CIP.logic import Util

#files_dir = sys.argv[1]
files_dir = "/Data/jonieva/tempdata/George_Subtype_Training/"
results_dir = path.join(files_dir, "Modified")
if not path.isdir(results_dir):
    # Create the results folder if it doesn't exist
    os.makedirs(results_dir)
files = os.listdir(files_dir)

types_delete = [97, 98, 99, 100]
types_replace = {
    94: 84,
    96: 85,
    101: 34,
    102: 86,
    103: 88
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
        points = []
        change_coords = geom.coordinate_system != geom.LPS
        for point in geom.points:
            if point.chest_type not in types_delete:
                if types_replace.has_key(point.chest_type):
                    # Replace type
                    point.chest_type = types_replace[point.chest_type]
                if change_coords:
                    print("B:replace ", point.coordinate)
                    # Switch to LPS (RAS will be assumed)
                    point.coordinate = Util.ras_to_lps(point.coordinate)
                    print("To: ", point.coordinate)
                points.append(point)
        # Replace the points
        geom.points = points
        geom.coordinate_system = geom.LPS
    # Save file
    xml = geom.to_xml()
    p = path.join(results_dir, file_name)
    with open(p, "w") as f:
        f.write(xml)