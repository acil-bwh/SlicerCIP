import os


def files_not_in(folder1, folder2, output_file, command="{}\n"):
    """ Compare two folders and generate a text file with the differences.
    At the moment it just says files in folder2 that are not in folder1 (uncomment for bidirectional)
    @param folder1:
    @param folder2:
    @param output_file: whole path to the output file
    """
    files1 = set(f for f in os.listdir(folder1) if f.endswith("parenchymaTraining.xml"))
    files2 = set(f for f in os.listdir(folder2) if f.endswith("parenchymaTraining.xml"))

    f1_not_in_f2 = files1.difference(files2)

    s = "# Files in {} that are not in {}:\n".format(folder1, folder2)
    for f in f1_not_in_f2:
        s += command.format(f)
    # s+="\nFiles in {} that are not in {}:\n".format(folder2, folder1)
    # s+="\n".join(f2_not_in_f1)
    print s
    with open(output_file, "w") as f:
        f.write(s)

def files_different(folder1, folder2, output_file, command="{}\n"):
    """Find files that are in folder1 and folder2 but whose size is different"""
    files1 = set(f for f in os.listdir(folder1) if f.endswith("parenchymaTraining.xml"))
    files2 = set(f for f in os.listdir(folder2) if f.endswith("parenchymaTraining.xml"))

    s = "# Files that are different in {} and {}:\n".format(folder1, folder2)
    for f in files1.intersection(files2):
        if os.path.getsize(os.path.join(folder1, f)) != os.path.getsize(os.path.join(folder2, f)):
            #s += f + "\n"
            s += command.format(f)
    print s
    with open(output_file, "w") as f:
        f.write(s)

def upload_to_MAD(input_folder, output_file):
    """ Upload all the xml files in input_folder to the corresponding MAD folder
    @param input_folder: folder that contains the xml files
    @param output_file: text file that will contain all the required scp commands
    """
    s = "# Upload of xml files to MAD\n"
    for file_name in os.listdir(input_folder):
        if file_name.endswith("_parenchymaTraining.xml"):
            s += "scp {} copd@mad-replicated1.research.partners.org:Processed/COPDGene/{}/{}\n".format(
                os.path.join(input_folder, file_name),
                file_name.split("_")[0],
                file_name.replace("_parenchymaTraining.xml", "")
            )

    print s
    with open(output_file, "w") as f:
        f.write(s)


#f1 = "/Data/jonieva/tempdata/parenchymaTraining/parenchymaTraining-acil"
#f2 = "/Data/jonieva/tempdata/parenchymaTraining/parenchymaTraining-acil-before removal"
f1 = "/Data/jonieva/Dropbox/ProjectsResources/parenchyma_classification/QC-Baseline/Rola"
f2 = "/Data/jonieva/Dropbox/ProjectsResources/parenchyma_classification/QC-Baseline/MAD"
output_file_q3 = "/Data/jonieva/Dropbox/ProjectsResources/parenchyma_classification/QC-Baseline/Quarantine3.sh"
output_file_q4 = "/Data/jonieva/Dropbox/ProjectsResources/parenchyma_classification/QC-Baseline/Quarantine4.sh"
command_q3 = "mv %s/{} %s/Quarantine3\n" % (f2, f2)
command_q4 = "cp %s/{} %s/Quarantine4\n" % (f1, f2)

# files_different(f1,f2, output_file_q3, command_q3)
# files_not_in(f1, f2, output_file_q4, command_q4)

output_file_upload_MAD = "/Data/jonieva/tempdata/parenchymaTraining/upload_to_MAD.sh"
upload_to_MAD(f2, output_file_upload_MAD)