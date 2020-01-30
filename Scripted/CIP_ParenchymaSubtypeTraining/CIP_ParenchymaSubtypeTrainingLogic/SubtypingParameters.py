from collections import OrderedDict

import slicer

from CIP.logic.SlicerUtil import SlicerUtil

class SubtypingParameters(object):
    """ Class that stores the structure required for Chest Subtyping training
    """
    # MAIN TYPES (Label, abbreviation, color)
    __types__ = OrderedDict()
    __types__[84] = ["ILD", "ILD", (1, 0.525, 0)]
    __types__[4] = ["Emphysema", "Emphysema", (0.24, 0.74, 1)]
    __types__[2] = ["Airway", "Airway", (0.097, 0.173, 1)]
    __types__[3] = ["Vessel", "Vessel", (1, 0, 0)]
    __types__[86] = ["Nodule", "Nodule", (0.49, 0, 0.88)]
    __types__[91] = ["Mesothelioma", "Meso", (0.8, 0.2, 0.8)]
    __types__[1] = ["Normal parenchyma", "Normal", (0.28, 0.77, 0.22)]

    @property
    def mainTypes(self):
        """"All the allowed main types"""
        return self.__types__

    # SUBTYPES
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
    __subtypes__[35] = ("Cyst", "Cyst")
    __subtypes__[90] = ("Fibronodular", "Fib")
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
    # Airway
    __subtypes__[77] = ("Bronchiectatic", "BE")
    __subtypes__[78] = ("Not bronchiectatic", "non-BE")
    __subtypes__[41] = ("Airway Gen.3", "A3")
    __subtypes__[42] = ("Airway Gen.4", "A4")
    __subtypes__[43] = ("Airway Gen.5", "A5")
    __subtypes__[44] = ("Airway Gen.6", "A6")
    __subtypes__[45] = ("Airway Gen.7", "A7")
    __subtypes__[46] = ("Airway Gen.8", "A8")
    __subtypes__[47] = ("Airway Gen.9", "A9")
    __subtypes__[48] = ("Airway Gen.10", "A10")
    __subtypes__[99] = ("Branch", "AB")
    __subtypes__[31] = ("Mucus Plug", "Mucus")

    # Vessel
    __subtypes__[50] = ("Artery", "Art")
    __subtypes__[51] = ("Vein", "Vein")
    __subtypes__[57] = ("Vessel Gen. 1", "VG1")
    __subtypes__[58] = ("Vessel Gen. 2", "VG2")
    __subtypes__[59] = ("Vessel Gen. 3", "VG3")
    __subtypes__[60] = ("Vessel Gen. 4", "VG4")
    __subtypes__[100] = ("Branch", "VB")



    # Nodule
    __subtypes__[87] = ("Benign nodule", "BN")
    __subtypes__[88] = ("Malign nodule", "Tumor")

    @property
    def subtypes(self):
        """All the allowed possible subtypes"""
        return self.__subtypes__


    # REGIONS
    __regions__ = OrderedDict()
    __regions__[0] = ("Any", "")

    # ILD, Emphysema, Vessel, Nodule
    __regions__[4] = ("Right Superior Lobe", "RSL")
    __regions__[5] = ("Right Middle Lobe", "RML")
    __regions__[6] = ("Right Inferior Lobe", "RIL")
    __regions__[7] = ("Left Superior Lobe", "LSL")
    __regions__[8] = ("Left Inferior Lobe", "LIL")
    __regions__[45] = ("Ascending Aorta", "AA")
    __regions__[46] = ("Transversal Aorta", "TA")
    __regions__[47] = ("Descending Aorta", "DA")
    __regions__[58] = ("Trachea", "Trachea")
    __regions__[76] = ("Carina", "Carina")


    @property
    def regions(self):
        """All the allowed possible regions"""
        return self.__regions__

    # ARTIFACTS
    __artifacts__ = OrderedDict()
    __artifacts__[0] = ("No artifact", "")
    __artifacts__[1] = ("Undefined", "Artifact")
    __artifacts__[4] = ("Motion", "Motion")

    @property
    def artifacts(self):
        return self.__artifacts__

    @property
    def totalAllowedCombinationsNumber(self):
        return len(self.__allowedCombinationsTypes__)

    # Allowed type combinations
    TYPE_INDEX = 0                           # Type (0-255)
    SUBTYPE_OR_REGION_INDEX = 1              # Subtype or region (0-255)

    __allowedCombinationsTypes__ = (
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
        (84, 35),
        (84, 90),
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
        (2, 41),
        (2, 42),
        (2, 43),
        (2, 44),
        (2, 45),
        (2, 46),
        (2, 47),
        (2, 48),
        (2, 99),
        (2, 31),
        # VESSEL
        (3, 0),
        (3, 50),
        (3, 51),
        (3, 57),
        (3, 58),
        (3, 59),
        (3, 60),
        (3, 100),
        # NODULE
        (86, 0),
        (86, 87),
        (86, 88),
        # MESOTHELIOMA
        (91, 0),
        # NORMAL
        (1, 0))

    # Allowed region combinations (not necessary at the moment)
    # __allowedCombinationsRegions__ = ( \
    #     # ILD
    #     (84, 0),
    #     (84, 7),
    #     # AIRWAY
    #     (2, 0),
    #     # VESSEL
    #     (3, 0),
    #     (3, 7),
    #     # NODULE
    #     (86, 0),
    #     # MESOTHELIOMA
    #     (91, 0),
    #     # NORMAL
    #     (1, 0))


    ## MAIN TYPES
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


    ## SUBTYPES
    def getSubtypes(self, typeId):
        """ Return the subtypes allowed for a concrete type
        :param typeId: type id
        :return: Dictionary with Key=subtype_id and Value=tuple with subtype features
        """
        d = OrderedDict()
        for item in (item for item in self.__allowedCombinationsTypes__ if item[self.TYPE_INDEX] == typeId):
            d[item[self.SUBTYPE_OR_REGION_INDEX]] = self.__subtypes__[item[self.SUBTYPE_OR_REGION_INDEX]]
        return d

    def getMainTypeForSubtype(self, subtypeId):
        """ Get the main type for a subtype (it returns the first one in case it's duplicated)
        :param subtypeId:
        :return:
        """
        for comb in self.__allowedCombinationsTypes__:
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
        :return: string
        """
        if subtypeId == 0:
            return ""
        return self.subtypes[subtypeId][1]


    ## REGIONS
    # def getRegions(self, typeId):
    #     """ Return the regions allowed for a concrete type
    #     :param typeId: type id
    #     :return: Dictionary with Key=region_id and Value=tuple with region features
    #     """
    #     d = OrderedDict()
    #     for item in (item for item in self.__allowedCombinationsRegions__ if item[self.TYPE_INDEX] == typeId):
    #         d[item[self.SUBTYPE_OR_REGION_INDEX]] = self.__regions__[item[self.SUBTYPE_OR_REGION_INDEX]]
    #     return d

    def getRegionLabel(self, regionId):
        """ Get regions like "Region (ABR)" with the description and abbreviation
        :param regionId: region id
        :return: string
        """
        if regionId == 0:
            return self.__subtypes__[0][0]
        return "{0} ({1})".format(self.__regions__[regionId][0], self.__regions__[regionId][1])

    def getRegionAbbreviation(self, regionId):
        """ Get the abbreviation for this region.
        :param regionId:
        :return:
        """
        if regionId == 0:
            return ""
        return self.__regions__[regionId][1]


    ## ARTIFACTS
    def getArtifactLabel(self, artifactId):
        """ At the moment just the description (it may change if we include useful abbreviations)
            :param artifactId:
            :return: string
        """
        return self.artifacts[artifactId][0]

    def getArtifactAbbreviation(self, artifactId):
        """ Get the abbreviation for this artifact.
            :return: string
        """
        return self.artifacts[artifactId][1]


    def getColor(self, typeId, artifactId):
        """ Get a  3-tuple color for this type and/or artifact
        :param typeId:
        :return: 3-color tuple (each color in the 0-1 range)
        """
        if artifactId != 0:
            return (1, 0, 0)       # Mark all artifacts as red
        return self.getMainTypeColor(typeId)

    def createColormapNode(self, colormapName):
        """ Create a colormap node with one color per type (plus Red for artifacts).
        :param colormapName: the colormap node will be named like this
        :return:
        """
        # Types/Regions (2 bytes)
        colorNode = SlicerUtil.createNewColormapNode(colormapName, numberOfColors=256**2)

        # Add background
        colorNode.SetColor(0, "Background", 0, 0, 0, 0)

        # Get Slicer GenericColors colormap node as a template
        slicerGenericColors = SlicerUtil.getNode('GenericColors')

        # Add a region and a type/subtype for each allowed combination
        # The regions will not have a special color, the type is the main object
        for typeId, subtypeId in self.__allowedCombinationsTypes__:
            t = subtypeId if subtypeId != 0 else typeId
            color = [0] * 4
            # Get the color from the RandomIntegers colormap
            slicerGenericColors.GetColor(t, color)
            t1 = self.getMainTypeLabel(typeId)
            t2 = self.getSubtypeLabel(subtypeId)

            typeLabel = "{}-{}".format(t1,t2) if subtypeId != 0 else t1
            for regionId in self.regions.keys():
                label = "{}-{}".format(typeLabel, self.regions[regionId][0]) if regionId != 0 else typeLabel
                colorId = (t << 8) + regionId
                colorNode.SetColor(colorId, label, color[0], color[1], color[2])


        # Add the regions. Use the same Random
        # for region in self.regions.iterkeys():
        #     color = [0] * 4
        #     slicerGenericColors.GetColor(region + 256, color)
        #     colorNode.SetColor(t, self.getRegionLabel(region), color[0], color[1], color[2])

        # Add Red (Artifact)
        # colorNode.SetColor(512, "ARTIFACT", 1.0, 0, 0)

        return colorNode