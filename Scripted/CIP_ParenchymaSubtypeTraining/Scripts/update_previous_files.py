""" Update a list of xml files because of changes in the xml format and redefinition of types agreed on 2015-09-08
"""
import sys, os
import os.path as path

# sys.path.append("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/")
from CIP.logic import geometry_topology_data as gtd
from CIP.logic import Util

#files_dir = sys.argv[1]
files_dir = "/Data/jonieva/tempdata/George_Subtype_Training/subset"
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
        for point[ in geom.points:
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


import os
from CIP.logic import Util
from os import path
import pprint
import CIP.logic.geometry_topology_data as gtd
#
#
#
# def detectOutOfExtentFiducials(xmls_dir, vols_dir):
xmls_dir = "/Data/jonieva/tempdata/parenchyma training/George/results/temp"
vols_dir = "/Data/jonieva/tempdata"
xmls = os.listdir(xmls_dir)
wrong_points = []
wrong_cases = set()
for file_name in xmls:
    if Util.get_file_extension(file_name) != ".xml":
        continue
    # Open volume
    volFile = "{0}/{1}.nhdr".format(vols_dir, file_name.replace("_parenchymaTraining.xml", ""))
    v = slicer.util.loadVolume(volFile, returnNode=True)[1]
    # print(volFile)
    dims = v.GetImageData().GetDimensions()
    p = path.join(xmls_dir, file_name)
    with open(p, "r+b") as f:
        xml = f.read()
        geom = gtd.GeometryTopologyData.from_xml(xml)
        for point in geom.points:
            ras = Util.lps_to_ras(point.coordinate)
            ijk = Util.ras_to_ijk(v, ras)
            for i in range(3):
                if ijk[i] < 0 or ijk[i] >= dims[i]:
                    # Flip just the second coord
                    # point.coordinate[1] = -point.coordinate[1]
                    wrong_points.append((file_name, point.coordinate, ijk))
                    wrong_cases.add(file_name)
        # if file_name in wrong_cases:
        #     print("Added " + file_name)
                # ras = point.coordinate
                # point.coordinate = Util.ras_to_lps(ras)

## Change sign
# for case in wrong_cases:
#     p = path.join(xmls_dir, case)
#     print ("Processing {0}...".format(p))
#     with open(p, "r+b") as f:
#         xml = f.read()
#         geom = gtd.GeometryTopologyData.from_xml(xml)
#         geom.num_dimensions = 3
#         points = []
#         for point in geom.points:
#             point.coordinate[1] = -point.coordinate[1]
#             points.append(point)
#         # Replace the points
#         geom.points = points
#         # Save file
#         resultspath = path.join(xmls_dir, "Modified", case)
#         xml = geom.to_xml()
#         with open(resultspath, "w") as f:
#             f.write(xml)
# return wrong_cases, wrong_points

#################################################################
# Add new fields
from xml.etree import ElementTree as etree
import xml.etree.ElementTree as et
import os.path as path
xmls_dir = "/Data/jonieva/Dropbox/ProjectsResources/parenchyma_classification/data/Training_points/ILD_trainingpoints-2015-10-20-postQC/"
output_dir = "/Data/jonieva/tempdata/tmp/updated"
xmls = os.listdir(xmls_dir)
timestamp = gtd.GeometryTopologyData.get_timestamp()
username = "gwashko"
machineName = "BatchProcess"
id = 1


for file_name in xmls:
    if Util.get_file_extension(file_name) != ".xml":
        continue
    id = 1
    p = path.join(xmls_dir, file_name)
    with open(p, "r+b") as f:
        xml = f.read()
    root = et.fromstring(xml)
    for xml_point_node in root.findall("Point"):
        s = "<Id>%i</Id>" % id
        xml_point_node.append(et.fromstring(s))
        s = "<Timestamp>%s</Timestamp>" % timestamp
        xml_point_node.append(et.fromstring(s))
        s = "<UserName>gwahsko</UserName>"
        xml_point_node.append(et.fromstring(s))
        s = "<MachineName>BATCH_PROCESS</MachineName>"
        xml_point_node.append(et.fromstring(s))
        id += 1

    new_xml = etree.tostring(root)
    p = path.join(output_dir, file_name)
    with open(p, "w+b") as f:
        f.write(new_xml)
    print(file_name + " processed")

def upload_to_MAD(input_folder):
    """ Upload all the xml files to the corresponding MAD folder
    @param input_folder:
    """
    total = ""
    for file_name in os.listdir(input_folder):
        if file_name.endswith("_parenchymaTraining.xml"):
            study = file_name.split("_")[-2]
            if study == "COPD":
                study = "COPDGene"
            elif study.startswith("DECAMP"):
                study = "DECAMP"
            s = "scp {} copd@mad-replicated1.research.partners.org:Processed/{}/{}/{}".format(
                os.path.join(input_folder, file_name),
                study,
                file_name.split("_")[0],
                file_name.replace("_parenchymaTraining.xml", "")
            )

            print s
            total += s + "\n"

    return total

s = upload_to_MAD("/Users/jonieva/Projects/acil/parenchymaTraining/")
with open("/Users/jonieva/Desktop/upload.sh", 'wb') as f:
    f.write(s)

# with open ("/Users/jonieva/Desktop/modified.txt", 'r') as f:
#     l = f.readlines()
#
# for i in range(len(l)):
#     l[i] = l[i].replace("parenchymaTraining/", "").strip()