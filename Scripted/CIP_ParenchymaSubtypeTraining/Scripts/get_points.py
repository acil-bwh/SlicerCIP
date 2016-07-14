def get_points(root_folder, study_name):
    import os
    import CIP.logic.geometry_topology_data as gtd
    points = 0
    for file_name in os.listdir(root_folder):
        if study_name in file_name:
            geom = gtd.GeometryTopologyData.from_xml_file(os.path.join(root_folder, file_name))
            points += len(geom.points)
    print "Total number of points: {}".format(points)


if  __name__ == "__main__":
    get_points("/Users/jonieva/Projects/acil-master/parenchymaTraining", "PLuSS")