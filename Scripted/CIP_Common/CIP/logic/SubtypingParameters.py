from collections import OrderedDict
  
class SubtypingParameters(object):
    """ Class that stores the structure required for Chest Subtyping training
    """
    #INF = 100000
    #MAX_REGION_TYPE_CODE = 65536  # 11111111 11111111
 
    """ Allowed region types """
    __types__ = OrderedDict()
    __types__[84] = "ILD"
    __types__[4] = "Emphysema"
    __types__[85] = "Artifact"

    @property
    def types(self):
        return self.__types__


    """ Allowed tissue types """
    __subtypes__ = OrderedDict()
    __subtypes__[0]  = ("Any", "")
    # ILD
    __subtypes__[86] = ("Subpleural line", "SpL")
    __subtypes__[87] = ("Reticular", "Rt")
    __subtypes__[88] = ("Reticular nodular", "RtN")
    __subtypes__[89] = ("Ground glass", "GrG")
    __subtypes__[90] = ("Honeycombing", "Hon")
    __subtypes__[91] = ("Centrilobular nodule", "Cen")
    __subtypes__[92] = ("Consolidation", "Con")
    __subtypes__[93] = ("Nodule", "N")
    __subtypes__[94] = ("Parenchymal band", "PB")
    __subtypes__[95] = ("Intralobular septal thickening", "IST")
    __subtypes__[96] = ("Subpleural cysts", "SpC")
    # EMPHYSEMA
    __subtypes__[10] = ("Mild paraseptal", "Mild Par")
    __subtypes__[11] = ("Moderate paraseptal", "Mod Par")
    __subtypes__[12] = ("Severe paraseptal", "Sev Par")
    __subtypes__[16] = ("Mild centrilobular", "Mild Cen")
    __subtypes__[17] = ("Moderate centrilobular", "Mod Cen")
    __subtypes__[18] = ("Severe centrilobular", "Sev Cen")
    __subtypes__[19] = ("Mild panlobular", "Mild Pan")
    __subtypes__[20] = ("Moderate panlobular", "Mod Pan")
    __subtypes__[21] = ("Severe panlobular", "Sev Pan")

    @property
    def subtypes(self):
        return self.__subtypes__


    # """ Allowed combinations.
    #   Structure of the object:
    #   - TypeId
    #   - SubtypeId
    #   - Red level (0-1)
    #   - Green level (0-1)
    #   - Blue level (0-1)
    #   """
    # TYPE_ID = 0                 # Type (0-255)
    # SUBTYPE_ID = 1              # Subtype (0-255)
    # RED = 2                     # Red level (0-1)
    # GREEN = 3                   # Green level (0-1)
    # BLUE = 4                    # Blue level (0-1)
    #
    # __allowedCombinations__ = ( \
    # # ILD
    # (84, 0, 1, 0, 0),
    # (84, 86, 1, 0, 0),
    # (84, 87, 0.9, 0, 0),
    # (84, 88, 0.8, 0, 0),
    # (84, 89, 0.7, 0, 0),
    # (84, 90, 0.6, 0, 0),
    # (84, 91, 0.5, 0, 0),
    # (84, 92, 0.4, 0, 0),
    # (84, 93, 0.35, 0, 0),
    # (84, 94, 0.3, 0, 0),
    # (84, 95, 0.25, 0, 0),
    # # EMPHYSEPMA
    # (4, 0, 0, 0, 1),
    # (4, 10, 0, 0, 1),
    # (4, 11, 0, 0, 0.8),
    # (4, 12, 0, 0, 0.6),
    # (4, 16, 0, 1, 1),
    # (4, 17, 0, 0.8, 0.8),
    # (4, 18, 0, 0.6, 0.6),
    # (4, 19, 0, 1, 0),
    # (4, 20, 0, 0.8, 0),
    # (4, 21, 0, 0.6, 0),
    # # ARTIFACT
    # (85, 0, 0.5, 0.5, 0.5))

    """ Allowed combinations.
      Structure of the object:
      - TypeId
      - SubtypeId

      """
    TYPE_ID = 0                 # Type (0-255)
    SUBTYPE_ID = 1              # Subtype (0-255)


    __allowedCombinations__ = ( \
        # ILD
        (84, 0),
        (84, 86),
        (84, 87),
        (84, 88),
        (84, 89),
        (84, 90),
        (84, 91),
        (84, 92),
        (84, 93),
        (84, 94),
        (84, 95),
        # EMPHYSEPMA
        (4, 0),
        (4, 10),
        (4, 11),
        (4, 12),
        (4, 16),
        (4, 17),
        (4, 18),
        (4, 19),
        (4, 20),
        (4, 21),
        # ARTIFACT
        (85, 0))


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
        d = {}
        for item in (item for item in self.__allowedCombinations__ if item[self.TYPE_ID] == typeId):
            d[item[self.SUBTYPE_ID]] = self.__subtypes__[item[self.SUBTYPE_ID]]
        return d

    def getSubtypeFullDescr(self, subtypeId):
        """ Get subtypes like "Subtype (ABR)" with the description and abbreviation
        :param subtypeId:
        :return: string
        """
        if subtypeId == 0:
            return self.__subtypes__[0][0]
        return "{0} ({1})".format(self.__subtypes__[subtypeId][0], self.__subtypes__[subtypeId][1])

    def getSubtypeAbbreviation(self, subtypeId):
        """ Get the abbreviation for this subtype
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
        if typeId == 84: return (0.133, 0.7, 0.193)     # ILD
        if typeId == 4: return (0, 0, 1)     # Emphysema
        if typeId == 85: return (1, 0, 0)     # Artifact
        return None