from __main__ import vtk, qt, ctk, slicer
import numpy as np
from collections import OrderedDict

class ParenchymalVolume:
    def __init__(self, parenchymaLabelmapArray, sphereWithoutTumorLabelmapArray, spacing, keysToAnalyze=None):
        """ Parenchymal volume study.
        Compare each ones of the different labels in the original labelmap with the volume of the area of interest
        :param parenchymaLabelmapArray: original labelmap for the whole volume node
        :param sphereWithoutTumorLabelmapArray: labelmap array that contains the sphere to study without the tumor
        :param spacing: tuple of volume spacing
        :param keysToAnalyze: list of strings with the types of emphysema it's going to be analyzed. When None,
            all the types will be analyzed
        """
        self.parenchymaLabelmapArray = parenchymaLabelmapArray
        self.sphereWithoutTumorLabelmapArray = sphereWithoutTumorLabelmapArray
        self.spacing = spacing
        self.parenchymalVolumeStatistics = OrderedDict()
        self.parenchymalVolumeStatisticsTiming = OrderedDict()

        allKeys = list(self.getAllEmphysemaTypes().keys())
        if keysToAnalyze is not None:
            self.keysToAnalyze = keysToAnalyze.intersection(allKeys)
        else:
            self.keysToAnalyze = list(self.getAllEmphysemaTypes().keys())

    @staticmethod
    def getAllEmphysemaTypes():
        """ All emphysema types and values
        :return: dictionary of Type(string)-[numeric_code, description]
        """
        return {
            "Emphysema": 5,
            "Mild paraseptal emphysema": 10,
            "Moderate paraseptal emphysema": 11,
            "Severe paraseptal emphysema": 12,
            "Mild centrilobular emphysema": 16,
            "Moderate centrilobular emphysema": 17,
            "Severe centilobular emphysema": 18,
            "Mild panlobular emphysema": 19,
            "Moderate panlobular emphysema": 20,
            "Severe panlobular emphysema": 21
        }

    @staticmethod
    def getAllEmphysemaDescriptions():
        return list(ParenchymalVolume.getAllEmphysemaTypes().keys())

    def analyzeType(self, code):
        print(("DEBUG: analyze code {0}.".format(code)))
        # Calculate volume for the studied ROI (tumor)
        totalVolume = np.sum(self.parenchymaLabelmapArray == code)
        if totalVolume == 0:
            return 0

        # Calculate total volume in the sphere for this emphysema type
        sphereVolume = np.sum(self.parenchymaLabelmapArray[self.sphereWithoutTumorLabelmapArray.astype(np.bool)] == code)

        # Result: SV / PV
        return float(sphereVolume) / totalVolume

    def EvaluateFeatures(self, printTiming = False, checkStopProcessFunction=None):
        # Evaluate dictionary elements corresponding to user-selected keys
        # Remove all the keys that must not be evaluated
        for key in set(self.parenchymalVolumeStatistics.keys()).difference(self.keys):
            self.parenchymalVolumeStatistics[key] = None

        types = self.getAllEmphysemaTypes()

        if not printTiming:
            for key in self.keysToAnalyze:
                self.parenchymalVolumeStatistics[key] = self.analyzeType(types[key])
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.parenchymalVolumeStatistics

        else:
            import time
            t1 = time.time()
            for key in self.keysToAnalyze:
                self.parenchymalVolumeStatistics[key] = self.analyzeType(types[key])
                self.parenchymalVolumeStatisticsTiming[key] = time.time() - t1
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.parenchymalVolumeStatistics, self.parenchymalVolumeStatisticsTiming
