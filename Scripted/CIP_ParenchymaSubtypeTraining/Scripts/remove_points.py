sys.path.append("/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common/")
from CIP.logic import geometry_topology_data as gtd
from CIP.logic import Util

import os
import os.path
import re

wrong_cases_path = "/Volumes/Mac500/Dropbox/rola-jorge/LH ROI failure/"
xmls_path = "/Volumes/Mac500/Dropbox/ACIL-Biomarkers/parenchyma training 2015-10-02/"
results_path = "/Volumes/Mac500/Data/tempdata/parenchyma training 2015-10-02/Removed Points/LH ROI failure"
current_case = ""
caseIds = dict()

for file_name in os.listdir(wrong_cases_path):
    if Util.get_file_extension(file_name) != ".png":
        continue
    expr = "(?P<caseid>(^(.*?)_(.*?)_(.*?)_(.*?)_(.*?)))_(.*?)_p(?P<point>(.*?))_(.*)"
    r = re.match(expr, file_name)
    caseId = r.group("caseid")
    point = int(r.group("point"))
    if not caseIds.has_key(caseId):
        caseIds[caseId] = []
    caseIds[caseId].append(point)

for caseId, excludedPoints in caseIds.iteritems():
    # Load the Geometry object
    geom = gtd.GeometryTopologyData.from_xml_file(os.path.join(xmls_path, caseId + "_parenchymaTraining.xml"))
    newPoints=[]
    for i in range(len(geom.points)):
        if i not in excludedPoints:
            newPoints.append(geom.points[i])
    geom.points = newPoints
    geom.to_xml_file(os.path.join(results_path, caseId + "_parenchymaTraining.xml"))
    print("{0}: {1} removed points".format(caseId, len(excludedPoints)))
