folder = "/Data/jonieva/tempdata/Sam/xmls_parenchymaTraining_2016_04_05"
def check_files(folder):
    import os
    for f in (f for f in os.listdir(folder) if f.split(".")[-1] == "xml"):
        with open(os.path.join(folder, f), "r") as  myfile:
            s = myfile.read()
            if "<ChestType>90" in s:
                print f
        # p = "ssh copd@mad-replicated1.research.partners.org ls Processed/COPDGene/10015T/10015T_INSP_STD_BWH_COPD"
        # sp = f.split("_")
        # study = sp[-2]
        # if study == "COPD":
        #     study = "COPDGene"
        #
        # p = "ssh copd@mad-replicated1.research.partners.org ls Processed/{0}/{1}/{2}/{3}".format(
        #     study, sp[0], f.replace("_parenchymaTraining.xml", ""), f)
        # print p
check_files(folder)