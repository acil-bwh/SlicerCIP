from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections
from functools import reduce


class MorphologyStatistics:
    def __init__(self, labelNodeSpacing, matrixSA, matrixSACoordinates, matrixSAValues, allKeys):
        self.morphologyStatistics = collections.OrderedDict()
        self.morphologyStatisticsTiming = collections.OrderedDict()
        self.morphologyStatistics["Volume mm^3"] = 'self.volumeMM3(self.matrixSAValues, self.cubicMMPerVoxel)'
        self.morphologyStatistics[
            "Volume cc"] = 'self.volumeCC(self.matrixSAValues, self.cubicMMPerVoxel, self.ccPerCubicMM)'
        self.morphologyStatistics[
            "Surface Area mm^2"] = 'self.surfaceArea(self.matrixSA, self.matrixSACoordinates, self.matrixSAValues, self.labelNodeSpacing)'
        self.morphologyStatistics[
            "Surface:Volume Ratio"] = 'self.surfaceVolumeRatio(self.morphologyStatistics["Surface Area mm^2"], self.morphologyStatistics["Volume mm^3"])'
        self.morphologyStatistics[
            "Compactness 1"] = 'self.compactness1(self.morphologyStatistics["Surface Area mm^2"], self.morphologyStatistics["Volume mm^3"])'
        self.morphologyStatistics[
            "Compactness 2"] = 'self.compactness2(self.morphologyStatistics["Surface Area mm^2"], self.morphologyStatistics["Volume mm^3"])'
        self.morphologyStatistics[
            "Maximum 3D Diameter"] = 'self.maximum3DDiameter(self.labelNodeSpacing, self.matrixSA, self.matrixSACoordinates)'
        self.morphologyStatistics[
            "Spherical Disproportion"] = 'self.sphericalDisproportion(self.morphologyStatistics["Surface Area mm^2"], self.morphologyStatistics["Volume mm^3"])'
        self.morphologyStatistics[
            "Sphericity"] = 'self.sphericityValue(self.morphologyStatistics["Surface Area mm^2"], self.morphologyStatistics["Volume mm^3"])'

        self.keys = set(allKeys).intersection(list(self.morphologyStatistics.keys()))

        self.labelNodeSpacing = labelNodeSpacing
        self.matrixSA = matrixSA
        self.matrixSACoordinates = matrixSACoordinates
        self.matrixSAValues = matrixSAValues


        self.cubicMMPerVoxel = reduce(lambda x, y: x * y, self.labelNodeSpacing)
        self.ccPerCubicMM = 0.001

    def volumeMM3(self, matrixSA, cubicMMPerVoxel):
        return (matrixSA.size * cubicMMPerVoxel)

    def volumeCC(self, matrixSA, cubicMMPerVoxel, ccPerCubicMM):
        return (matrixSA.size * cubicMMPerVoxel * ccPerCubicMM)

    def surfaceArea(self, a, matrixSACoordinates, matrixSAValues, labelNodeSpacing):
        x, y, z = labelNodeSpacing
        xz = x * z
        yz = y * z
        xy = x * y
        voxelTotalSA = (2 * xy + 2 * xz + 2 * yz)
        totalSA = matrixSAValues.size * voxelTotalSA

        # in matrixSACoordinates
        # i corresponds to height (z)
        # j corresponds to vertical (y)
        # k corresponds to horizontal (x)

        i, j, k = 0, 0, 0
        surfaceArea = 0
        for voxel in range(0, matrixSAValues.size):
            i, j, k = matrixSACoordinates[0][voxel], matrixSACoordinates[1][voxel], matrixSACoordinates[2][voxel]
            fxy = (numpy.array([a[i + 1, j, k], a[i - 1, j, k]]) == 0)  # evaluate to 1 if true, 0 if false
            fyz = (numpy.array([a[i, j + 1, k], a[i, j - 1, k]]) == 0)  # evaluate to 1 if true, 0 if false
            fxz = (numpy.array([a[i, j, k + 1], a[i, j, k - 1]]) == 0)  # evaluate to 1 if true, 0 if false
            surface = (numpy.sum(fxz) * xz) + (numpy.sum(fyz) * yz) + (numpy.sum(fxy) * xy)
            surfaceArea += surface
        return (surfaceArea)

    def surfaceVolumeRatio(self, surfaceArea, volumeMM3):
        return (surfaceArea / volumeMM3)

    def compactness1(self, surfaceArea, volumeMM3):
        return ((volumeMM3) / ((surfaceArea) ** (2 / 3.0) * math.sqrt(math.pi)))

    def compactness2(self, surfaceArea, volumeMM3):
        return ((36 * math.pi) * ((volumeMM3) ** 2) / ((surfaceArea) ** 3))

    def maximum3DDiameter(self, labelNodeSpacing, matrixSA, matrixSACoordinates):
        # largest pairwise euclidean distance between tumor surface voxels

        x, y, z = labelNodeSpacing

        minBounds = numpy.array(
            [numpy.min(matrixSACoordinates[0]), numpy.min(matrixSACoordinates[1]), numpy.min(matrixSACoordinates[2])])
        maxBounds = numpy.array(
            [numpy.max(matrixSACoordinates[0]), numpy.max(matrixSACoordinates[1]), numpy.max(matrixSACoordinates[2])])

        a = numpy.array(list(zip(*matrixSACoordinates)))
        edgeVoxelsMinCoords = numpy.vstack(
            [a[a[:, 0] == minBounds[0]], a[a[:, 1] == minBounds[1]], a[a[:, 2] == minBounds[2]]]) * [z, y, x]
        edgeVoxelsMaxCoords = numpy.vstack(
            [(a[a[:, 0] == maxBounds[0]] + 1), (a[a[:, 1] == maxBounds[1]] + 1), (a[a[:, 2] == maxBounds[2]] + 1)]) * [
                                  z, y, x]

        maxDiameter = 1
        for voxel1 in edgeVoxelsMaxCoords:
            for voxel2 in edgeVoxelsMinCoords:
                voxelDistance = numpy.sqrt(numpy.sum((voxel2 - voxel1) ** 2))
                if voxelDistance > maxDiameter:
                    maxDiameter = voxelDistance
        return (maxDiameter)

    def sphericalDisproportion(self, surfaceArea, volumeMM3):
        R = ((0.75 * (volumeMM3)) / (math.pi) ** (1 / 3.0))
        return ((surfaceArea) / (4 * math.pi * (R ** 2)))

    def sphericityValue(self, surfaceArea, volumeMM3):
        return (((math.pi) ** (1 / 3.0) * (6 * volumeMM3) ** (2 / 3.0)) / (surfaceArea))

    def EvaluateFeatures(self, printTiming=False, checkStopProcessFunction=None):
        # Evaluate dictionary elements corresponding to user-selected keys
        if not self.keys:
            return self.morphologyStatistics

        if len(self.matrixSA) == 0:
            for key in self.keys:
                self.morphologyStatistics[key] = 0
        else:
            # Volume and Surface Area are pre-calculated even if only one morphology metric is user-selected
            if printTiming:
                import time
                t1 = time.time()
            self.morphologyStatistics["Volume mm^3"] = eval(self.morphologyStatistics["Volume mm^3"])
            self.keys.add("Volume mm^3")
            if printTiming:
                self.morphologyStatisticsTiming["Volume mm^3"] = time.time() - t1
            self.morphologyStatistics["Surface Area mm^2"] = eval(self.morphologyStatistics["Surface Area mm^2"])
            self.keys.add("Surface Area mm^2")
            if printTiming:
                t1 = time.time()
                self.morphologyStatisticsTiming["Surface Area mm^2"] = time.time() - t1

            # Remove all the keys that must not be evaluated
            for key in set(self.morphologyStatistics.keys()).difference(self.keys):
                self.morphologyStatistics[key] = None

            if printTiming:
                for key in self.keys:
                    if isinstance(self.morphologyStatistics[key], str):
                        t1 = time.time()
                        self.morphologyStatistics[key] = eval(self.morphologyStatistics[key])
                        self.morphologyStatisticsTiming[key] = time.time() - t1
                        if checkStopProcessFunction is not None:
                            checkStopProcessFunction()
                return self.morphologyStatistics, self.morphologyStatisticsTiming
            else:
                for key in self.keys:
                    if isinstance(self.morphologyStatistics[key], str):
                        self.morphologyStatistics[key] = eval(self.morphologyStatistics[key])
                        if checkStopProcessFunction is not None:
                            checkStopProcessFunction()
               
                return self.morphologyStatistics
