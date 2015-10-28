from collections import OrderedDict
  
class SubtypingParameters(object):
    """ Class that stores the structure required for Chest Subtyping training
    """
    # MAIN TYPES (Label, abbreviation, color)
    """ Allowed region types """
    __types__ = OrderedDict()
    __types__[84] = ["ILD", "ILD", (1, 0.525, 0)]
    __types__[4] = ["Emphysema", "Emphysema", (0.24, 0.74, 1)]
    __types__[2] = ["Airway", "Airway", (0.097, 0.173, 1)]
    __types__[86] = ["Nodule", "Nodule", (0.49, 0, 0.88)]
    __types__[1] = ["Normal parenchyma", "Normal", (0.28, 0.77, 0.22)]

    @property
    def mainTypes(self):
        return self.__types__

    # SUBTYPES
    """ Allowed tissue types """
    __subtypes__ = OrderedDict()
    __subtypes__[0]  = ("Any", "")
    # ILD
    __subtypes__[85] = ("Subpleural line", "SpL")
    __subtypes__[6] = ("Reticular", "Ret")
    __subtypes__[7] = ("Nodular", "Nodr")
    __subtypes__[5] = ("Ground glass", "GG")
    __subtypes__[37] = ("Honeycombing", "Hon")
    __subtypes__[26] = ("Centrilobular nodule", "Cen")
    __subtypes__[86] = ("Nodule", "Nod")
    __subtypes__[34] = ("Linear scar", "Lin")
    # Emphysema
    __subtypes__[67] = ("Paraseptal", "PSE")
    __subtypes__[68] = ("Centrilobular", "CLE")
    __subtypes__[69] = ("Panlobular", "PLE")
    __subtypes__[10] = ("Mild paraseptal", "Mild PSE")
    __subtypes__[11] = ("Moderate paraseptal", "Mod PSE")
    __subtypes__[12] = ("Severe paraseptal", "Sev PSE")
    __subtypes__[16] = ("Mild centrilobular", "Mild CLE")
    __subtypes__[17] = ("Moderate centrilobular", "Mod CLE")
    __subtypes__[18] = ("Severe centrilobular", "Sev CLE")
    __subtypes__[19] = ("Mild panlobular", "Mild PLE")
    __subtypes__[20] = ("Moderate panlobular", "Mod PLE")
    __subtypes__[21] = ("Severe panlobular", "Sev PLE")
    # Bronchiestatic
    __subtypes__[77] = ("Bronchiectatic", "BE")
    __subtypes__[78] = ("Not bronchiectatic", "non-BE")
    # Nodule
    __subtypes__[87] = ("Benign nodule", "BN")
    __subtypes__[88] = ("Malign nodule", "Tumor")


    @property
    def subtypes(self):
        return self.__subtypes__

    # ARTIFACTS
    __artifacts__ = OrderedDict()
    __artifacts__[0] = ("No artifact", "")
    __artifacts__[1] = ("Undefined", "Artifact")
    __artifacts__[4] = ("Motion", "Motion")

    @property
    def artifacts(self):
        return self.__artifacts__



    """ Allowed combinations"""
    TYPE_ID = 0                 # Type (0-255)
    SUBTYPE_ID = 1              # Subtype (0-255)

    __allowedCombinations__ = ( \
        # ILD
        (84, 0),
        (84, 85),
        (84, 6),
        (84, 7),
        (84, 5),
        (84, 37),
        (84, 26),
        (84, 86),
        (84, 34),
        # EMPHYSEPMA
        (4, 0),
        (4, 67),
        (4, 68),
        (4, 69),
        (4, 10),
        (4, 11),
        (4, 12),
        (4, 16),
        (4, 17),
        (4, 18),
        (4, 19),
        (4, 20),
        (4, 21),
        # AIRWAY
        (2, 0),
        (2, 77),
        (2, 78),
        # NODULE
        (86, 0),
        (86, 87),
        (86, 88),
        # ARTIFACT
        #(95, 0),
        # NORMAL
        (1, 0))


    def getMainTypes(self):
        """ Return all the main types
        :return: Ordered dict of main types
        """
        return self.__types__

    def getMainTypeLabel(self, typeId):
        """ Get the regular label for this type
        :param typeId: main type id
        :return: string
        """
        return self.mainTypes[typeId][0]

    def getMainTypeAbbreviation(self, typeId):
        """ Get the abbreviation for this type
        :param typeId: main type id
        :return: string
        """
        return self.mainTypes[typeId][1]

    def getMainTypeColor(self, typeId):
        """ Get a tuple with the color for this type
        :param typeId: main type id
        :return: 3-tuple 0-1 values
        """
        return self.mainTypes[typeId][2]


    def getSubtypes(self, typeId):
        """ Return the subtypes allowed for a concrete type
        :param type: type id
        :return: Dictionary with Key=subtype_id and Value=tuple with subtype features
        """
        d = OrderedDict()
        for item in (item for item in self.__allowedCombinations__ if item[self.TYPE_ID] == typeId):
            d[item[self.SUBTYPE_ID]] = self.__subtypes__[item[self.SUBTYPE_ID]]
        return d

    def getMainTypeForSubtype(self, subtypeId):
        """ Get the main type for a subtype (it returns the first one in case it's duplicated)
        :param subtypeId:
        :return:
        """
        for comb in self.__allowedCombinations__:
            if comb[1] == subtypeId: return comb[0]
        return None

    def getSubtypeLabel(self, subtypeId):
        """ Get subtypes like "Subtype (ABR)" with the description and abbreviation
        :param subtypeId:
        :return: string
        """
        if subtypeId == 0:
            return self.__subtypes__[0][0]
        return "{0} ({1})".format(self.__subtypes__[subtypeId][0], self.__subtypes__[subtypeId][1])

    def getSubtypeAbbreviation(self, subtypeId):
        """ Get the abbreviation for this subtype.
        :param subtypeId:
        :return:
        """
        if subtypeId == 0:
            return ""
        return self.subtypes[subtypeId][1]


    def getArtifactLabel(self, artifactId):
        """ At the moment just the description (it may change if we include useful abbreviations)
            :param artifactId:
            :return: string
        """
        return self.artifacts[artifactId][0]

    def getArtifactAbbreviation(self, artifactId):
        """ Get the abbreviation for this artifact.
            :param subtypeId:
            :return:
        """
        return self.artifacts[artifactId][1]


    def getColor(self, typeId, artifactId):
        """ Get a  3-tuple color for this type and/or artifact
        :param typeId:
        :return:
        """
        if artifactId != 0:
            return (1, 0, 0)       # Mark all artifacts as red
        return self.getMainTypeColor(typeId)
        # if typeId == 84: return (1, 0.525, 0)     # ILD
        # if typeId == 4: return (0.24, 0.74, 1)     # Emphysema
        # if typeId == 2: return (0.44, 0.42, 0.2)     # Airway
        # # if typeId == 95: return (1, 0, 0)     # Artifact
        # if typeId == 1: return (0.28, 0.77, 0.22)     # Normal
        # raise Exception("Unknown color for type {0}".format(typeId))