import sys
import os
import CIP.logic.geometry_topology_data as gtd

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

def remove_duplicated_case(points_list):
    """
    Take a list of points and remove duplicates
    @param points_list:
    @return: list of points without duplicates and set of removed points ids
    """
    duplicated = set()
    copy_list = sorted(points_list, key=lambda p: (p.coordinate[0], p.coordinate[1], p.coordinate[2]))
    for i in range(len(copy_list)):
        for j in range(i + 1, len(copy_list)):
            if copy_list[i].coordinate[0] == copy_list[j].coordinate[0] \
                    and copy_list[i].coordinate[1] == copy_list[j].coordinate[1] \
                    and copy_list[i].coordinate[2] == copy_list[j].coordinate[2]:
                duplicated.add(copy_list[j].id)
            else:
                break
    if len(duplicated) > 0:
        # duplicated_total[file_name] = duplicated
        removed = set()
        copy_list = list()

        for point in points_list:
            if point.id in duplicated:
                if point.id not in removed:
                    # Keep the first instance
                    removed.add(point.id)
                    copy_list.append(point)
            else:
                copy_list.append(point)

    return copy_list, duplicated

def remove_duplicated_points(root_folder):
    """
    Remove all the duplicated points in a folder with XMLs (the files will be overwritten)
    @param root_folder:
    @return: dict with filename and set of duplicated points
    """
    duplicated_total = {}
    for file_name in os.listdir(root_folder):
        if file_name.endswith(".xml"):
            geom = gtd.GeometryTopologyData.from_xml_file(os.path.join(root_folder, file_name))
            filtered_points, duplicated = remove_duplicated_case(geom.points)
            if duplicated > 0:
                # Replace file in place
                geom.points = sorted(filtered_points, key = lambda p: p.id)
                geom.to_xml_file(os.path.join(root_folder, file_name))
                print("File %s replaced" % file_name)
                duplicated_total[file_name] = duplicated
    return duplicated_total


def merge_files(f1, f2, output_file):
    """
    Merge all the points that are in f1 and f2 GeometryTopologyData xml files
    @param f1:
    @param f2:
    @return: list of merged points
    """
    g1 = gtd.GeometryTopologyData.from_xml_file(f1)
    g2 = gtd.GeometryTopologyData.from_xml_file(f2)

    p1 = sorted(g1.points, key=lambda p: p.id)
    p2 = sorted(g2.points, key=lambda p: p.id)

    m1 = p1[len(p1)-1].id if len(p1) > 0 else 1
    for p in p2:
        p.__id__ += m1
        p1.append(p)

    g1.points = p1
    g1.to_xml_file(output_file)
    return p1

def merge_directory(d1, d2, dout):
    """
    Merge all the xmls in tow directories, saving the result in "dout" folder
    @param d1:
    @param d2:
    @param dout:
    @return:
    """
    # Get the common files
    import glob
    import filecmp
    import shutil

    print "Merging {} and {} in {}".format(d1, d2, dout)
    s1 = set(map(lambda x: os.path.basename(x), glob.glob(os.path.join(d1, "*.xml"))))
    # print "d1 files: ", s1
    s2 = set(map(lambda x: os.path.basename(x), glob.glob(os.path.join(d2, "*.xml"))))

    snew = s2.difference(s1)
    for f in snew:
        shutil.copy(os.path.join(d2, f), os.path.join(d1, f))
        print "File {} added".format(f)

    # print "d2 files: ", s2
    s1 = s1.union(snew)
    s3 = s1.intersection(s2)

    merged = 0
    for f in s3:
        f1 = os.path.join(d1, f)
        f2 = os.path.join(d2, f)
        if filecmp.cmp(f1, f2):
            print "File {} skipped".format(f)
        else:
            out = os.path.join(dout, f)
            merge_files(f1, f2, out)
            print "File {} MERGED".format(f)
            merged += 1
    print "Total number of merged files: {}. New files: {}".format(merged, len(snew))


if  __name__ == "__main__":
    # patients, points = get_points_type("/Users/jonieva/Projects/acil/parenchymaTraining/", "DECAMP", 2)
    # print points
    # print patients
    # print len(patients)

    root_folder = "/Users/jonieva/Projects/acil/parenchymaTraining/"
    #root_folder = "/Data/jonieva/tempdata/tmp/"
    dups = remove_duplicated_points(root_folder)
    print dups

