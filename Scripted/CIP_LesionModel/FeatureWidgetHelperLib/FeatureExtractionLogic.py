from __main__ import vtk, qt, ctk, slicer

import math
import operator
import numpy as np
import collections


from . import *
import FeatureExtractionLib

class FeatureExtractionLogic:
    def __init__(self, volumeNode, volumeNodeArray, labelmapNodeArray, featureCategoriesKeys, featureKeys):
        self.volumeNode = volumeNode
        self.volumeNodeArray = volumeNodeArray
        self.labelmapNodeArray = labelmapNodeArray
        self.featureCategoriesKeys = featureCategoriesKeys
        self.featureKeys = featureKeys
        # initialize Progress Bar
        self.progressBar = qt.QProgressDialog(slicer.util.mainWindow())
        self.progressBar.minimumDuration = 0
        self.progressBar.show()
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(len(self.featureKeys))
        self.progressBar.labelText = 'Calculating for %s: ' % self.volumeNode.GetName()

        self.__analysisResultsDict__ = None

    @property
    def AnalysisResultsDict(self):
        """ Dictionary with FeatureKey-FeatureValue for all the analysis performed
        :return:
        """
        return self.__analysisResultsDict__

    def run(self):
        """ Run all the selected analysis
        :return: Dictionary of Feature-Value with all the features analyzed
        """
        # create Numpy Arrays
        # self.nodeArrayVolume = self.createNumpyArray(self.volumeNode)
        # self.nodeArrayLabelMapROI = self.createNumpyArray(self.labelmapNode)

        # extract voxel coordinates (ijk) and values from self.dataNode within the ROI defined by self.labelmapNode
        self.targetVoxels, self.targetVoxelsCoordinates = self.tumorVoxelsAndCoordinates(self.labelmapNodeArray, self.volumeNodeArray)

        # create a padded, rectangular matrix with shape equal to the shape of the tumor
        self.matrix, self.matrixCoordinates = self.paddedTumorMatrixAndCoordinates(self.targetVoxels, self.targetVoxelsCoordinates)

        # get Histogram data
        self.bins, self.grayLevels, self.numGrayLevels = self.getHistogramData(self.targetVoxels)

        ########
        # Manage feature classes for Heterogeneity feature calculations and consolidate into self.FeatureVector
        # TODO: create a parent class for all feature classes
        self.__analysisResultsDict__ = collections.OrderedDict()

        # Node Information
        # self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Node Information", len(self.__featureDict__))
        # self.nodeInformation = FeatureExtractionLib.NodeInformation(self.dataNode, self.labelmapNode, self.featureKeys)
        # self.__featureDict__.update( self.nodeInformation.EvaluateFeatures() )

        # First Order Statistics
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "First Order Statistics", len(self.__analysisResultsDict__))
        self.firstOrderStatistics = FeatureExtractionLib.FirstOrderStatistics(self.targetVoxels, self.bins, self.numGrayLevels, self.featureKeys)
        self.__analysisResultsDict__.update( self.firstOrderStatistics.EvaluateFeatures() )

        # Shape/Size and Morphological Features)
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "Morphology Statistics", len(self.__analysisResultsDict__))
        # extend padding by one row/column for all 6 directions
        maxDimsSA = tuple(map(operator.add, self.matrix.shape, ([2,2,2])))
        matrixSA, matrixSACoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDimsSA, self.targetVoxels)
        self.morphologyStatistics = FeatureExtractionLib.MorphologyStatistics(self.volumeNode.GetSpacing(), matrixSA, matrixSACoordinates, self.targetVoxels, self.featureKeys)
        self.__analysisResultsDict__.update( self.morphologyStatistics.EvaluateFeatures() )

        # Texture Features(GLCM)
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "GLCM Texture Features", len(self.__analysisResultsDict__))
        self.textureFeaturesGLCM = FeatureExtractionLib.TextureGLCM(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys)
        self.__analysisResultsDict__.update( self.textureFeaturesGLCM.EvaluateFeatures() )

        # Texture Features(GLRL)
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "GLRL Texture Features", len(self.__analysisResultsDict__))
        self.textureFeaturesGLRL = FeatureExtractionLib.TextureGLRL(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys)
        self.__analysisResultsDict__.update( self.textureFeaturesGLRL.EvaluateFeatures() )

        # Geometrical Measures
        # TODO: progress bar does not update to Geometrical Measures while calculating (create separate thread?)
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "Geometrical Measures", len(self.__analysisResultsDict__))
        self.geometricalMeasures = FeatureExtractionLib.GeometricalMeasures(self.volumeNode.GetSpacing(), self.matrix, self.matrixCoordinates, self.targetVoxels, self.featureKeys)
        self.__analysisResultsDict__.update( self.geometricalMeasures.EvaluateFeatures() )

        # Renyi Dimensions
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "Renyi Dimensions", len(self.__analysisResultsDict__))
        # extend padding to dimension lengths equal to next power of 2
        maxDims = tuple( [int(pow(2, math.ceil(np.log2(np.max(self.matrix.shape)))))] * 3 )
        matrixPadded, matrixPaddedCoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDims, self.targetVoxels)
        self.renyiDimensions = FeatureExtractionLib.RenyiDimensions(matrixPadded, matrixPaddedCoordinates, self.featureKeys)
        self.__analysisResultsDict__.update( self.renyiDimensions.EvaluateFeatures() )

        # close progress bar
        self.updateProgressBar(self.progressBar, self.volumeNode.GetName(), "Populating Summary Table", len(self.__analysisResultsDict__))
        self.progressBar.close()
        self.progressBar = None

        # filter for user-queried features only
        self.__analysisResultsDict__ = collections.OrderedDict((k, self.__analysisResultsDict__[k]) for k in self.featureKeys)

        return self.__analysisResultsDict__

    # def createNumpyArray (self, imageNode):
    #     # Generate Numpy Array from vtkMRMLScalarVolumeNode
    #     imageData = vtk.vtkImageData()
    #     imageData = imageNode.GetImageData()
    #     shapeData = list(imageData.GetDimensions())
    #     shapeData.reverse()
    #     return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))

    def tumorVoxelsAndCoordinates(self, arrayROI, arrayDataNode):
        coordinates = np.where(arrayROI != 0) # can define specific label values to target or avoid
        values = arrayDataNode[coordinates].astype('int64')
        return(values, coordinates)

    def paddedTumorMatrixAndCoordinates(self, targetVoxels, targetVoxelsCoordinates):
        ijkMinBounds = np.min(targetVoxelsCoordinates, 1)
        ijkMaxBounds = np.max(targetVoxelsCoordinates, 1)
        matrix = np.zeros(ijkMaxBounds - ijkMinBounds + 1)
        matrixCoordinates = tuple(map(operator.sub, targetVoxelsCoordinates, tuple(ijkMinBounds)))
        matrix[matrixCoordinates] = targetVoxels
        return(matrix, matrixCoordinates)

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

    def updateProgressBar(self, progressBar, nodeName, nextFeatureString, totalSteps):
        slicer.app.processEvents()
        progressBar.labelText = 'Calculating %s: %s' % (nodeName, nextFeatureString)
        progressBar.setValue(totalSteps)


