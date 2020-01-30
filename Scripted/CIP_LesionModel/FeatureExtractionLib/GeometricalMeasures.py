from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator
import collections
from functools import reduce


class GeometricalMeasures:
    def __init__(self, labelNodeSpacing, parameterMatrix, parameterMatrixCoordinates, parameterValues, allKeys):
        # need non-linear scaling of surface heights for normalization (reduce computational time)
        self.GeometricalMeasures = collections.OrderedDict()
        self.GeometricalMeasuresTiming = collections.OrderedDict()
        self.GeometricalMeasures[
            "Extruded Surface Area"] = "self.extrudedSurfaceArea(self.labelNodeSpacing, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues)"
        self.GeometricalMeasures[
            "Extruded Volume"] = "self.extrudedVolume(self.extrudedMatrix, self.extrudedMatrixCoordinates, self.cubicMMPerVoxel)"
        self.GeometricalMeasures[
            "Extruded Surface:Volume Ratio"] = "self.extrudedSurfaceVolumeRatio(self.labelNodeSpacing, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues, self.cubicMMPerVoxel)"

        self.labelNodeSpacing = labelNodeSpacing
        self.parameterMatrix = parameterMatrix
        self.parameterMatrixCoordinates = parameterMatrixCoordinates
        self.parameterValues = parameterValues
        self.keys = set(allKeys).intersection(list(self.GeometricalMeasures.keys()))

        if self.keys:
            self.cubicMMPerVoxel = reduce(lambda x, y: x * y, labelNodeSpacing)
            self.extrudedMatrix, self.extrudedMatrixCoordinates = self.extrudeMatrix(self.parameterMatrix,
                                                                                     self.parameterMatrixCoordinates,
                                                                                     self.parameterValues)

    def extrudedSurfaceArea(self, labelNodeSpacing, extrudedMatrix, extrudedMatrixCoordinates, parameterValues):
        x, y, z = labelNodeSpacing

        # surface areas of directional connections
        xz = x * z
        yz = y * z
        xy = x * y
        fourD = (2 * xy + 2 * xz + 2 * yz)

        totalVoxelSurfaceArea4D = (2 * xy + 2 * xz + 2 * yz + 2 * fourD)
        totalSA = parameterValues.size * totalVoxelSurfaceArea4D

        # in matrixSACoordinates
        # i: height (z), j: vertical (y), k: horizontal (x), l: 4th or extrusion dimension
        i, j, k, l = 0, 0, 0, 0
        extrudedSurfaceArea = 0

        # vectorize
        for i, j, k, l_slice in zip(*extrudedMatrixCoordinates):
            for l in range(l_slice.start, l_slice.stop):
                fxy = numpy.array([extrudedMatrix[i + 1, j, k, l], extrudedMatrix[i - 1, j, k, l]]) == 0
                fyz = numpy.array([extrudedMatrix[i, j + 1, k, l], extrudedMatrix[i, j - 1, k, l]]) == 0
                fxz = numpy.array([extrudedMatrix[i, j, k + 1, l], extrudedMatrix[i, j, k - 1, l]]) == 0
                f4d = numpy.array([extrudedMatrix[i, j, k, l + 1], extrudedMatrix[i, j, k, l - 1]]) == 0

                extrudedElementSurface = (numpy.sum(fxz) * xz) + (numpy.sum(fyz) * yz) + (numpy.sum(fxy) * xy) + (
                numpy.sum(f4d) * fourD)
                extrudedSurfaceArea += extrudedElementSurface
        return (extrudedSurfaceArea)

    def extrudedVolume(self, extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel):
        extrudedElementsSize = extrudedMatrix[numpy.where(extrudedMatrix == 1)].size
        return (extrudedElementsSize * cubicMMPerVoxel)

    def extrudedSurfaceVolumeRatio(self, labelNodeSpacing, extrudedMatrix, extrudedMatrixCoordinates, parameterValues,
                                   cubicMMPerVoxel):
        extrudedSurfaceArea = self.extrudedSurfaceArea(labelNodeSpacing, extrudedMatrix, extrudedMatrixCoordinates,
                                                       parameterValues)
        extrudedVolume = self.extrudedVolume(extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel)
        return (extrudedSurfaceArea / extrudedVolume)

    def extrudeMatrix(self, parameterMatrix, parameterMatrixCoordinates, parameterValues):
        # extrude 3D image into a binary 4D array with the intensity or parameter value as the 4th Dimension
        # need to normalize CT images with a shift of 120 Hounsfield units

        parameterValues = numpy.abs(parameterValues)

        # maximum intensity/parameter value appended as shape of 4th dimension
        extrudedShape = parameterMatrix.shape + (numpy.max(parameterValues),)

        # pad shape by 1 unit in all 8 directions
        extrudedShape = tuple(map(operator.add, extrudedShape, [2, 2, 2, 2]))

        extrudedMatrix = numpy.zeros(extrudedShape)
        extrudedMatrixCoordinates = tuple(map(operator.add, parameterMatrixCoordinates, ([1, 1, 1]))) + (
        numpy.array([slice(1, value + 1) for value in parameterValues]),)
        for slice4D in zip(*extrudedMatrixCoordinates):
            extrudedMatrix[slice4D] = 1
        return (extrudedMatrix, extrudedMatrixCoordinates)

    def EvaluateFeatures(self, printTiming=False, checkStopProcessFunction=None):
        # Evaluate dictionary elements corresponding to user-selected keys
        # Remove all the keys that must not be evaluated
        for key in set(self.GeometricalMeasures.keys()).difference(self.keys):
            self.GeometricalMeasures[key] = None

        if not self.keys:
            return self.GeometricalMeasures

        if printTiming:
            import time
            for key in self.keys:
                t1 = time.time()
                self.GeometricalMeasures[key] = eval(self.GeometricalMeasures[key])
                self.GeometricalMeasuresTiming[key] = time.time() - t1
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()

            return self.GeometricalMeasures, self.GeometricalMeasuresTiming
        else:
            for key in self.keys:
                self.GeometricalMeasures[key] = eval(self.GeometricalMeasures[key])
                if checkStopProcessFunction is not None:
                    checkStopProcessFunction()
            return self.GeometricalMeasures
