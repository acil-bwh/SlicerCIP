from collections import OrderedDict
  
class SubtypingParameters(object):
    """ Class that stores the structure required for Chest Subtyping training
    """
    #INF = 100000
    #MAX_REGION_TYPE_CODE = 65536  # 11111111 11111111
 
    """ Allowed region types """
    __types__ = OrderedDict()
    __types__[94] = "ILD"
    __types__[4] = "Emphysema"
    __types__[2] = "Airway"
    __types__[95] = "Artifact"
    __types__[1] = "Normal"


    @property
    def mainTypes(self):
        return self.__types__


    """ Allowed tissue types """
    __subtypes__ = OrderedDict()
    __subtypes__[0]  = ("Any", "")
    # ILD
    __subtypes__[96] = ("Subpleural line", "SpL")
    __subtypes__[6] = ("Reticular", "Ret")
    __subtypes__[97] = ("Reticular nodular", "RetN")
    __subtypes__[5] = ("Ground glass", "GG")
    __subtypes__[37] = ("Honeycombing", "Hon")
    __subtypes__[26] = ("Centrilobular nodule", "Cen")
    __subtypes__[98] = ("Consolidation", "Con")
    __subtypes__[7] = ("Nodule", "Nod")
    # __subtypes__[94] = ("Parenchymal band", "PB")
    # __subtypes__[95] = ("Intralobular septal thickening", "IST")
    # __subtypes__[96] = ("Subpleural cysts", "SpC")
    __subtypes__[99] = ("Paraseptal emphysema with ground glass", "PSE-GG")
    __subtypes__[100] = ("Centrilobular emphysema with ground glass", "CLE-GG")
    __subtypes__[101] = ("Linear", "Lin")

    # EMPHYSEMA
    __subtypes__[67] = ("Paraseptal", "PSE")
    __subtypes__[68] = ("Centrilobular", "CLE")
    __subtypes__[69] = ("Panlobular", "PLE")
    # __subtypes__[10] = ("Mild paraseptal", "Mild PSE")
    # __subtypes__[11] = ("Moderate paraseptal", "Mod PSE")
    # __subtypes__[12] = ("Severe paraseptal", "Sev PSE")
    # __subtypes__[16] = ("Mild centrilobular", "Mild CLE")
    # __subtypes__[17] = ("Moderate centrilobular", "Mod CLE")
    # __subtypes__[18] = ("Severe centrilobular", "Sev CLE")
    # __subtypes__[19] = ("Mild panlobular", "Mild PLE")
    # __subtypes__[20] = ("Moderate panlobular", "Mod PLE")
    # __subtypes__[21] = ("Severe panlobular", "Sev PLE")

    # BRONCHIESTATIC
    __subtypes__[77] = ("Bronchiectatic", "BE")
    __subtypes__[78] = ("Not bronchiectatic", "non-BE")



    @property
    def subtypes(self):
        return self.__subtypes__


    """ Allowed combinations"""
    TYPE_ID = 0                 # Type (0-255)
    SUBTYPE_ID = 1              # Subtype (0-255)

    __allowedCombinations__ = ( \
        # ILD
        (94, 0),
        (94, 96),
        (94, 6),
        (94, 97),
        (94, 5),
        (94, 37),
        (94, 26),
        (94, 98),
        (94, 7),
        (94, 99),
        (94, 100),
        (94, 101),
        # (84, 97),
        # (84, 98),
        # (84, 99),
        # EMPHYSEPMA
        (4, 0),
        (4, 67),
        (4, 68),
        (4, 69),
        # (4, 10),
        # (4, 11),
        # (4, 12),
        # (4, 16),
        # (4, 17),
        # (4, 18),
        # (4, 19),
        # (4, 20),
        # (4, 21),
        # (4, 97),
        # (4, 98),
        # AIRWAY
        (2, 0),
        (2, 77),
        (2, 78),
        # ARTIFACT
        (95, 0),
        # NORMAL
        (1, 0))


    def getMainTypes(self):
        """ Return all the main types
        :return: Ordered dict of main types
        """
        return self.__types__

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

    def getSubtypeFullDescr(self, subtypeId):
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

    def getColor(self, typeId):
        """ Get a  3-tuple color for this type
        :param typeId:
        :return:
        """
        if typeId == 94: return (0.93, 0.9, 0.26)     # ILD
        if typeId == 4: return (0.24, 0.74, 1)     # Emphysema
        if typeId == 2: return (0.44, 0.42, 0.2)     # Airway
        if typeId == 95: return (1, 0, 0)     # Artifact
        if typeId == 1: return (0.28, 0.77, 0.22)     # Normal
        raise Exception("Unknown color for type {0}".format(typeId))