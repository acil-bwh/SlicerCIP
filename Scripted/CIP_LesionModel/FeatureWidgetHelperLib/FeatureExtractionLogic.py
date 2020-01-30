from __main__ import vtk, qt, ctk, slicer

import math
import operator
import numpy as np
import collections
import time
import logging
from . import *
import FeatureExtractionLib

class FeatureExtractionLogic:
    def __init__(self, volumeNode, labelmapROIArray, featureCategoriesKeys, featureKeys, additionalProgressbarDesc="",
                 labelmapWholeVolumeArray=None):
        """
        :param volumeNode: VTK intensities volume node
        :param volumeNodeArray: numpy array that represents volumeNode
        :param labelmapROIArray: numpy array with the labelmap of the area to study (ex: tumor)
        :param featureCategoriesKeys: main categories that have some feature that is going to be analyzed
        :param featureKeys: features that are going to be analyzed
        :param additionalProgressbarDesc: additional description that will be displayed in the progress bar
            for each one of the main categories while the analysis is performed
        :param labelmapWholeVolumeArray: numpy array that represents a labelmap for the whole volume (different
            from 'labelMapROIArray' that represents just the area of interest that is going to be analyzed)
        :return:
        """
        self.volumeNode = volumeNode
        self.volumeNodeArray = slicer.util.array(self.volumeNode.GetID())
        self.labelmapROIArray = labelmapROIArray
        self.featureCategoriesKeys = featureCategoriesKeys
        self.featureKeys = featureKeys
        self.additionalProgressbarDesc = additionalProgressbarDesc
        self.labelmapWholeVolumeArray = labelmapWholeVolumeArray

        # initialize Progress Bar
        self.progressBar = qt.QProgressDialog(slicer.util.mainWindow())
        self.progressBar.minimumDuration = 0

        self.__analysisResultsDict__ = None
        self.__analysisTimingDict__ = None

    @property
    def AnalysisResultsDict(self):
        """ Dictionary with FeatureKey-FeatureValue for all the analysis performed
        :return:
        """
        return self.__analysisResultsDict__

    @property
    def AnalysisTimingsDict(self):
        """ Dictionary with FeatureKey-FeatureValue for all the analysis performed
        :return:
        """
        return self.__analysisTimingDict__

    def run(self, resultsStorage, printTiming=False, resultsStorageTiming=None):
        """ Run all the selected analysis
        :return:
            If printTiming==False: Dictionary of Feature-Value with all the features analyzed
            else: tuple with 2 dictionaries (1 of Feature-Value and another one with Feature-Timing)
        """
        self.progressBar.show()
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(len(self.featureKeys))
        self.progressBar.labelText = 'Calculating for {0}{1}: '.format(self.volumeNode.GetName(), self.additionalProgressbarDesc)

        #print("DEBUG: running the following categories: ", self.featureCategoriesKeys)
        #print("DEBUG: running the following features: ", self.featureKeys)

        # create Numpy Arrays
        # self.nodeArrayVolume = self.createNumpyArray(self.volumeNode)
        # self.nodeArrayLabelMapROI = self.createNumpyArray(self.labelmapNode)
        t1 = time.time()
        # extract voxel coordinates (ijk) and values from self.dataNode within the ROI defined by self.labelmapNode
        self.targetVoxels, self.targetVoxelsCoordinates = self.tumorVoxelsAndCoordinates(self.labelmapROIArray, self.volumeNodeArray)
        if printTiming:
            print(("Time to calculate tumorVoxelsAndCoordinates: {0} seconds".format(time.time() - t1)))
        self.checkStopProcess()

        # create a padded, rectangular matrix with shape equal to the shape of the tumor
        t1 = time.time()
        self.matrix, self.matrixCoordinates = self.paddedTumorMatrixAndCoordinates(self.targetVoxels, self.targetVoxelsCoordinates)
        if printTiming:
            print(("Time to calculate paddedTumorMatrixAndCoordinates: {0} seconds".format(time.time() - t1)))
        self.checkStopProcess()

        # get Histogram data
        t1 = time.time()
        self.bins, self.grayLevels, self.numGrayLevels = self.getHistogramData(self.targetVoxels)
        if printTiming:
            print(("Time to calculate histogram: {0} seconds".format(time.time() - t1)))
        self.checkStopProcess()

        ########
        # self.__analysisResultsDict__ = collections.OrderedDict()
        # self.__analysisTimingDict__ = collections.OrderedDict()
        self.__analysisResultsDict__ = resultsStorage
        if printTiming:
            self.__analysisTimingDict__ = resultsStorageTiming
        progressBarDesc = self.volumeNode.GetName() + self.additionalProgressbarDesc

        # First Order Statistics
        if "First-Order Statistics" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "First-Order Statistics", len(self.__analysisResultsDict__))
            self.firstOrderStatistics = FeatureExtractionLib.FirstOrderStatistics(self.targetVoxels, self.bins, self.numGrayLevels, self.featureKeys)
            t1 = time.time()
            results = self.firstOrderStatistics.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate First Order Statistics: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Shape/Size and Morphological Features)
        if "Morphology and Shape" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "Morphology and Shape Statistics",
                                   len(self.__analysisResultsDict__))
            # extend padding by one row/column for all 6 directions
            if len(self.matrix) == 0:
                matrixSA = self.matrix
                matrixSACoordinates = self.matrixCoordinates
            else:
                maxDimsSA = tuple(map(operator.add, self.matrix.shape, ([2,2,2])))
                matrixSA, matrixSACoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDimsSA, self.targetVoxels)
            self.morphologyStatistics = FeatureExtractionLib.MorphologyStatistics(self.volumeNode.GetSpacing(), matrixSA, matrixSACoordinates, self.targetVoxels, self.featureKeys)
            t1 = time.time()
            results = self.morphologyStatistics.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Morphology and Shape: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Texture Features(GLCM)
        if "Texture: GLCM" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "GLCM Texture Features", len(self.__analysisResultsDict__))
            self.textureFeaturesGLCM = FeatureExtractionLib.TextureGLCM(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys, self.checkStopProcess)
            t1 = time.time()
            results =self.textureFeaturesGLCM.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Texture: GLCM: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Texture Features(GLRL)
        if "Texture: GLRL" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "GLRL Texture Features", len(self.__analysisResultsDict__))
            self.textureFeaturesGLRL = FeatureExtractionLib.TextureGLRL(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys)
            t1 = time.time()
            results =self.textureFeaturesGLRL.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Texture: GLRL: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Geometrical Measures
        if "Geometrical Measures" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "Geometrical Measures", len(self.__analysisResultsDict__))
            self.geometricalMeasures = FeatureExtractionLib.GeometricalMeasures(self.volumeNode.GetSpacing(), self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys)
            t1 = time.time()
            results =self.geometricalMeasures.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Geometrical Measures: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Renyi Dimensions
        if "Renyi Dimensions" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "Renyi Dimensions", len(self.__analysisResultsDict__))
            # extend padding to dimension lengths equal to next power of 2
            maxDims = tuple( [int(pow(2, math.ceil(np.log2(np.max(self.matrix.shape)))))] * 3 )
            matrixPadded, matrixPaddedCoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDims, self.targetVoxels)
            self.renyiDimensions = FeatureExtractionLib.RenyiDimensions(matrixPadded, matrixPaddedCoordinates, self.featureKeys)
            t1 = time.time()
            results =self.renyiDimensions.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Renyi Dimensions: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # Parenchymal Volume
        if "Parenchymal Volume" in self.featureCategoriesKeys:
            self.updateProgressBar(progressBarDesc, "Parenchymal Volume", len(self.__analysisResultsDict__))
            self.parenchymalVolume = FeatureExtractionLib.ParenchymalVolume(self.labelmapWholeVolumeArray, self.labelmapROIArray,
                                                        self.volumeNode.GetSpacing(), self.featureKeys)
            t1 = time.time()
            results =self.parenchymalVolume.EvaluateFeatures(printTiming, self.checkStopProcess)
            if printTiming:
                self.__analysisResultsDict__.update(results[0])
                self.__analysisTimingDict__.update(results[1])
                print(("Time to calculate Parenchymal Volume: {0} seconds".format(time.time() - t1)))
            else:
                self.__analysisResultsDict__.update(results)

        # close progress bar
        self.updateProgressBar(progressBarDesc, "Populating Summary Table", len(self.__analysisResultsDict__))
        self.progressBar.close()
        self.progressBar = None

        # filter for user-queried features only
        self.__analysisResultsDict__ = collections.OrderedDict((k, self.__analysisResultsDict__[k]) for k in self.featureKeys)

        if not printTiming:
            return self.__analysisResultsDict__
        else:
            return self.__analysisResultsDict__, self.__analysisTimingDict__


    def tumorVoxelsAndCoordinates(self, arrayROI, arrayDataNode):
        coordinates = np.where(arrayROI != 0) # can define specific label values to target or avoid
        values = arrayDataNode[coordinates].astype('int64')
        return(values, coordinates)

    def paddedTumorMatrixAndCoordinates(self, targetVoxels, targetVoxelsCoordinates):
        if len(targetVoxels) == 0:
            # Nothing to analyze
            empty = np.array([])
            return (empty, (empty, empty, empty))

        ijkMinBounds = np.min(targetVoxelsCoordinates, 1)
        ijkMaxBounds = np.max(targetVoxelsCoordinates, 1)
        matrix = np.zeros(ijkMaxBounds - ijkMinBounds + 1)
        matrixCoordinates = tuple(map(operator.sub, targetVoxelsCoordinates, tuple(ijkMinBounds)))
        matrix[matrixCoordinates] = targetVoxels
        return (matrix, matrixCoordinates)

    def getHistogramData(self, voxelArray):
        # with np.histogram(), all but the last bin is half-open, so make one extra bin container
        binContainers = np.arange(voxelArray.min(), voxelArray.max()+2)
        bins = np.histogram(voxelArray, bins=binContainers)[0] # frequencies
        grayLevels = np.unique(voxelArray) # discrete gray levels
        numGrayLevels = grayLevels.size
        return (bins, grayLevels, numGrayLevels)

    def padMatrix(self, a, matrixCoordinates, dims, voxelArray):
        # pads matrix 'a' with zeros and resizes 'a' to a cube with dimensions increased to the next greatest power of 2
        # numpy version 1.7 has np.pad function

        # center coordinates onto padded matrix    # consider padding with NaN or eps = np.spacing(1)
        pad = tuple(map(operator.div, tuple(map(operator.sub, dims, a.shape)), ([2,2,2])))
        matrixCoordinatesPadded = tuple(map(operator.add, matrixCoordinates, pad))
        matrix2 = np.zeros(dims)
        matrix2[matrixCoordinatesPadded] = voxelArray
        return (matrix2, matrixCoordinatesPadded)

    def updateProgressBar(self, nodeName, nextFeatureString, totalSteps):
        self.checkStopProcess()
        self.progressBar.labelText = 'Calculating %s: %s' % (nodeName, nextFeatureString)
        self.progressBar.setValue(totalSteps)
        slicer.app.processEvents()

    def checkStopProcess(self):
        slicer.app.processEvents()
        if self.progressBar.wasCanceled:
            self.progressBar.deleteLater()
            raise StopIteration("Progress cancelled!!!")

