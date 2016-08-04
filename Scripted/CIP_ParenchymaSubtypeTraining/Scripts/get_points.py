import sys
sys.path.append('/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_ParenchymaSubtypeTraining')
sys.path.append('/Users/jonieva/Projects/SlicerCIP/Scripted/CIP_Common')

def get_points(root_folder, study_name):
    import os
    import CIP.logic.geometry_topology_data as gtd
    points = 0
    for file_name in os.listdir(root_folder):
        if study_name in file_name:
            geom = gtd.GeometryTopologyData.from_xml_file(os.path.join(root_folder, file_name))
            points += len(geom.points)
    print "Total number of points: {}".format(points)

def get_points_type(root_folder, study_name, typeId):
    import os
    import CIP.logic.geometry_topology_data as gtd
    points = 0
    patients = set()
    from CIP_ParenchymaSubtypeTrainingLogic import SubtypingParameters
    s = SubtypingParameters.SubtypingParameters()
    subtypes = s.getSubtypes(typeId)
    subtypes[typeId] = 0

    print "Subtypes: ", subtypes

    for file_name in os.listdir(root_folder):
        if study_name in file_name:
            geom = gtd.GeometryTopologyData.from_xml_file(os.path.join(root_folder, file_name))
            p = gtd.Point
            for point in geom.points:
                if point.chest_type in subtypes:
                    points += 1
                    patients.add(file_name)

    return patients, points


if  __name__ == "__main__":
    patients, points = get_points_type("/Users/jonieva/Projects/acil/parenchymaTraining/", "DECAMP", 2)
    print points
    print patients
    print len(patients)