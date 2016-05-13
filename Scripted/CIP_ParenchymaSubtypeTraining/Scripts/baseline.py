import os


def files_not_in(folder1, folder2):
    """ Compare two folders and generate a text file with the differences.
    At the moment it just says files in folder2 that are not in folder1 (uncomment for bidirectional)
    @param folder1:
    @param folder2:
    @param output_file: whole path to the output file
    """
    files1 = set(f for f in os.listdir(folder1) if f.endswith("parenchymaTraining.xml"))
    files2 = set(f for f in os.listdir(folder2) if f.endswith("parenchymaTraining.xml"))

    f1_not_in_f2 = files1.difference(files2)

    s = "Files in {} that are not in {}:\n".format(folder1, folder2)
    s += "\n".join(f1_not_in_f2)
    # f2_not_in_f1 = files2.difference(files1)
    # s+="\nFiles in {} that are not in {}:\n".format(folder2, folder1)
    # s+="\n".join(f2_not_in_f1)
    print s

def files_different(folder1, folder2):
    """Find files that are in folder1 and folder2 but the size is different"""
    files1 = set(f for f in os.listdir(folder1) if f.endswith("parenchymaTraining.xml"))
    files2 = set(f for f in os.listdir(folder2) if f.endswith("parenchymaTraining.xml"))

    s = "Files that are different in {} and {}:\n".format(folder1, folder2)
    for f in files1.intersection(files2):
        if os.path.getsize(os.path.join(folder1, f)) != os.path.getsize(os.path.join(folder2, f)):
            s += f + "\n"

    print s

f1 = "/Data/jonieva/tempdata/parenchymaTraining/parenchymaTraining-acil/"
f2 = "/Data/jonieva/tempdata/parenchymaTraining/parenchymaTraining-acil-before removal/"

files_different(f1, f2)
