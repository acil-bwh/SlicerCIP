'''
Created on Oct 29, 2014
Common functions that can be useful in any Python module development
'''

#from __main__ import vtk
import vtk
import os, sys
# import shutil
import traceback
import numpy as np

#from CIP.logic import SlicerUtil

class Util: 
    # # Constants
    # CIP_MODULE_ROOT_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../..')
    # #CIP_GIT_REPO_FOLDER = os.path.realpath(CIP_MODULE_ROOT_DIR + '/../CIP-Repo')
    # CIP_DEFAULT_GIT_REPO_FOLDER = slicer.app.temporaryPath + '/CIP-Repo'
    # CIP_GIT_REMOTE_URL = "https://acilgeneric:bwhacil2015@github.com/acil-bwh/ACILSlicer.git"
    # #CIP_GIT_REPO = "/Users/Jorge/tmp/CIP-Repo"
    # CIP_LIBRARY_ROOT_DIR = CIP_MODULE_ROOT_DIR + '/CIP'
    #
    # ACIL_RESOURCES_DIR = CIP_LIBRARY_ROOT_DIR + '/ui/Resources'
    # CIP_ICON_DIR = ACIL_RESOURCES_DIR + '/Icons'

    OK = 0
    ERROR = 1

    AUTO_UPDATE_DISABLED = True

    @staticmethod
    def printLastException():
        """ Print in console the debug information for the last Exception occurred
        :return:
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "*** EXCEPTION OCCURRED: "
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
    
    @staticmethod
    def vtkToNumpyArray(vtkImageData):
        '''Get a numpy array from a VTK image data volume.
        The order is: slice, row, column (Z,Y,X).
        UPGRADE: if we receive a vtkMRMLScalarVolumeNode (like a labelmap) we can now just invoke a = slicer.util.array(node.GetName()) 
        If we manipulate the array, the changes will reflect in the vtkNode calling node.GetImageData().Modified()
        '''    
        shape = list(vtkImageData.GetDimensions())
        shape.reverse()
        numpyarray = vtk.util.numpy_support.vtk_to_numpy(vtkImageData.GetPointData().GetScalars()).reshape(shape)
        return numpyarray

    @staticmethod
    def getDimensions(vtkMRMLVolumeNode):
        """ Return a list of 3 positions with the dimensions of the volume (XYZ)
        :param vtkMRMLVolumeNode: vtkMRMLVolumeNode or any subclass
        :return: list of 3 integer positions
        """
        # Get bounds in RAS format
        bounds = [0,0,0,0,0,0]
        vtkMRMLVolumeNode.GetRASBounds(bounds)
        # Convert the limits to IJK format
        rastoijk=vtk.vtkMatrix4x4()
        vtkMRMLVolumeNode.GetRASToIJKMatrix(rastoijk)
        bounds = [bounds[0],bounds[2],bounds[5], 1]
        dimensions = rastoijk.MultiplyPoint(bounds)
        return [int(round(dimensions[0])), int(round(dimensions[1])), int(round(dimensions[2]))]

    @staticmethod
    def isWindows():
        """ Current system platform is Windows based
        :return:
        """
        return os.sys.platform == "win32"

    @staticmethod 
    def getLabelmapSlices(vtkImageData):
        '''Get a dictionary with the slices where all the label data are contained.
        The output will be a dictionary of [label_Code: array of labels].
        The origin is a vktImageData node'''
        # Get a numpy array from the imageData
        npArray = Util.vtkToNumpyArray(vtkImageData)
        # Extract labelmaps
        return Util.getLabelmapSlicesFromNumpyArray(npArray)
    
    @staticmethod
    def getLabelmapSlicesFromNumpyArray(npArray):
        '''Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 1: "2 steps" process compressing the array. It works much better when there are few slices with data'''
        #start = time.clock()
        # Get an array with the slices that contain any data
        positions = np.where(npArray > 0)
        slices = np.unique(positions[0])
         
        # Build a new array just with the slices that contain data
        boundArray = npArray[slices,:,:]
         
        # Search for all the different label maps
        labelMaps = np.unique(boundArray)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the slices that contain the label
            s = np.where(boundArray == label)
            # "Translate" to the true slice numbers and store the result
            result[label] = slices[np.unique(s[0])] 
        
    #     end = time.clock()
    #     print ("getLabelmapSlicesFromNumpyArray took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod 
    def getLabelmapSlicesFromNumpyArray2(npArray):
        '''Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 2: without compressing the array using projections'''
        #start = time.clock()     
        # Search for all the different label maps
        labelMaps = np.unique(npArray)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the labelmaps with projections
            result[label] = Util.getSlicesForLabelFromNumpyArray(npArray, label) 
        
    #     end = time.clock()
    #     print ("getLabelmapSlicesFromNumpyArray (method2) took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod 
    def getLabelmapSlicesFromNumpyArray3(npArray):
        '''Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 3: without compressing the array using where (VERY SLOW!)'''
        #start = time.clock() 
         
        # Search for all the different label maps
        labelMaps = np.unique(npArray)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the slices that contain the label
            s = np.where(npArray == label)
            # "Translate" to the true slice numbers and store the result
            result[label] = np.unique(s[0]) 
        
    #     end = time.clock()
    #     print ("getLabelmapSlicesFromNumpyArray (method2) took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod
    def getSlicesForLabel(vtkImageData, label):
        '''Return a numpy array with all the slices that contain the specified label. The origin is a vktImageData node'''
        # Get a numpy array from the imageData
        npArray = Util.vtkToNumpyArray(vtkImageData)
        # Get the results
        return Util.getSlicesForLabelFromNumpyArray(npArray)
    
    @staticmethod 
    def getSlicesForLabelFromNumpyArray(npArray, label):
        '''Get a numpyArray with the slices where label appears. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        '''
        # Get an array with the slices that contain this label
        t = (npArray == label)
        # Make a double projection to get the slices that contain the label
        tproj = t.any(axis=1)
        tproj = tproj.any(axis=1)
         
        # Return the indexes of the slices with data
        return np.where(tproj)[0]    
    


    @staticmethod
    def getLabelmapFromScalar(vtkMRMLScalarVolumeNode, nodeName=""):
        """ Convert a vtkMRMLScalarVolumeNode node in an equivalent vtkMRMLLabelMapVolumeNode
        :param vtkMRMLScalarVolumeNode:
        :param nodeName: name of the result node (default: scalarNodeName_lm)
        :return: vtkMRMLLabelMapVolumeNode
        """
        logic = slicer.modules.volumes.logic()
        if nodeName == "":
            nodeName = vtkMRMLScalarVolumeNode.GetName() + "_labelmap"

        node = logic.CreateAndAddLabelVolume(vtkMRMLScalarVolumeNode, nodeName)
        # Make sure that the node name is correct, because sometimes the scene adds a suffix
        node.SetName(nodeName)
        return node

    @staticmethod
    def RAStoIJK(volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk=vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        cl = list(rasCoords)
        cl.append(1)
        return list(rastoijk.MultiplyPoint(cl))


    @staticmethod
    def IJKtoRAS(volumeNode, ijkCoords):
        """ Transform a list of IJK coords in RAS for a volume
        :return: list of RAS coordinates
        """
        ijktoras=vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijktoras)
        cl = list(ijkCoords)
        cl.append(1)
        return list(ijktoras.MultiplyPoint(cl))


