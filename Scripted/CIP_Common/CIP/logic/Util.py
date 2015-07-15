'''
Created on Oct 29, 2014
Common functions that can be useful in any Python module development
'''

from __main__ import vtk, slicer
import numpy as np
import os
import shutil
#import time

class Util: 
    # Constants    
    CIP_MODULE_ROOT_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../..')
    #CIP_GIT_REPO_FOLDER = os.path.realpath(CIP_MODULE_ROOT_DIR + '/../CIP-Repo')
    CIP_DEFAULT_GIT_REPO_FOLDER = slicer.app.temporaryPath + '/CIP-Repo'
    CIP_GIT_REMOTE_URL = "https://acilgeneric:bwhacil2015@github.com/acil-bwh/ACILSlicer.git"
    #CIP_GIT_REPO = "/Users/Jorge/tmp/CIP-Repo"
    CIP_LIBRARY_ROOT_DIR = CIP_MODULE_ROOT_DIR + '/CIP'

    DATA_DIR = CIP_LIBRARY_ROOT_DIR + '/ui/Resources'
    ICON_DIR = DATA_DIR + '/Icons' 

    OK = 0
    ERROR = 1

    AUTO_UPDATE_DISABLED = True
    
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
    def saveNewNode(vtkMRMLScalarVolumeNode, fileName):
        """Save a new scalar node in a file and add it to the scene"""
        storageNode = vtkMRMLScalarVolumeNode.CreateDefaultStorageNode()
        storageNode.SetScene(slicer.mrmlScene)
        slicer.mrmlScene.AddNode(storageNode)
        vtkMRMLScalarVolumeNode.SetAndObserveStorageNodeID(storageNode.GetID())         
        storageNode.SetFileName(fileName)         
        # Save the file
        storageNode.WriteData(vtkMRMLScalarVolumeNode)
    
    @staticmethod    
    def settingGetOrSetDefault(settingName, settingDefaultValue):
        """Try to find the value of a setting and, if it does not exist, set ot to the defaultValue"""
        setting = slicer.app.settings().value(settingName)
        if setting != None:
            return setting    # The setting was already initialized
        
        slicer.app.settings().setValue(settingName, settingDefaultValue)
        return settingDefaultValue
    
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
    def gitUpdateCIP():
        if Util.AUTO_UPDATE_DISABLED:
            print("CIP auto update is disabled")
            return False

        #try:
        update = Util.__gitUpdate__()
        if update:
            # Copy the directory under CIP_GIT_REPO with this module name
            #srcPath = "%s/%s" %    (Util.CIP_GIT_REPO_FOLDER, moduleName)
            srcPath = Util.CIP_DEFAULT_GIT_REPO_FOLDER
            print('src: ', srcPath)
            #destPath = os.path.join(Util.CIP_LIBRARY_ROOT_DIR, moduleName)
            destPath = os.path.realpath(Util.CIP_MODULE_ROOT_DIR + '/..')
            print('dest: ', destPath)
            # First rename the folder to a temp name, as a backup
            backupPath = destPath + "_TMP"
            os.rename(destPath, backupPath)
            # Copy the folder
            shutil.copytree(srcPath, destPath)
            # Remove the temp folder
            shutil.rmtree(backupPath)
        
        return update
#         except Exception as ex:
#             print (ex.message())
#             return False

    @staticmethod
    def __gitUpdate__():
        '''Gets the last version of the CIP git repository.
        In case it does not exist, it creates it from scratch
        Returns true if there was any update in the repository'''
        from git import Repo

        if os.path.exists(Util.CIP_DEFAULT_GIT_REPO_FOLDER):
            # Check for updates
            repo = Repo(Util.CIP_DEFAULT_GIT_REPO_FOLDER)
            #remote = repo.remotes.pop()
            remote = repo.remotes.origin
            prevCommit = repo.head.commit.hexsha
            status = remote.fetch().pop()
            if status and status.commit.hexsha != prevCommit:
                remote.pull()
                return True
            
            return False
            
        else:
            # Create the new repository
            os.makedirs(Util.CIP_DEFAULT_GIT_REPO_FOLDER)
            os.chmod(Util.CIP_DEFAULT_GIT_REPO_FOLDER, 0777)
            #repo = Repo(Util.CIP_GIT_REPO_FOLDER)
            Repo.clone_from(Util.CIP_GIT_REMOTE_URL, Util.CIP_DEFAULT_GIT_REPO_FOLDER)
            print ("Created folder %s (first time update)" % Util.CIP_DEFAULT_GIT_REPO_FOLDER)
            # Always update the first time
            return True

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


    @staticmethod
    def padVolumeWithAnotherVolume(bigVolume, smallVolume, backgroundValue=None):
        """ Build a volume that will duplicate the information contained in "smallVolume", but
        it will be padded with a background value (by default the minimum value found in "bigVolume")
        to fit the size of "bigVolume".
        It will also respect the position where the small volume is inside the big volume.
        This method works for regular scalar nodes and also for labelmap nodes
        :param bigVolume: volume that will be used to set the position and size of the result volume
        :param smallVolume: information that will be really cloned
        :param backgroundValue: value to fill the rest of the volume that will contain no information
            (default: min value of bigVolume)
        :return: new volume with the dimensions of "bigVolume" but the information in "smallVolume"
        """
        # Get the position of the origin in the small volume in the big one
        origin = Util.RAStoIJK(bigVolume, smallVolume.GetOrigin())
        # Create a copy of the big volume to have the same spacial information
        #vlogic = slicer.modules.volumes.logic()
        #resultVolume = vlogic.CloneVolume(bigVolume, smallVolume.GetName() + "_extended")
        resultVolume = Util.cloneVolume(bigVolume, smallVolume.GetName() + "_extended")

        # Get the numpy arrays to operate with them
        npb = slicer.util.array(resultVolume.GetName())
        nps = slicer.util.array(smallVolume.GetName())
        # Initialize the big volume to the backround value or the minimum value of the big volume (default)
        if backgroundValue is None:
            back = npb.min()
            npb[:] = back
        else:
            npb[:] = backgroundValue
        # Copy the values of the small volume in the big one
        # Create the indexes
        x0 = int(origin[0])
        x1 = x0 + nps.shape[2]
        y0 = int(origin[1])
        y1 = y0 + nps.shape[1]
        z0 = int(origin[2])
        z1 = z0 + nps.shape[0]
        # Copy values
        npb[z0:z1, y0:y1, x0:x1] = nps[:,:,:]
        # Refresh values in mrml
        resultVolume.GetImageData().Modified()
        # Return the result volume
        return resultVolume

    @staticmethod
    def cloneVolume(volumeNode, copyVolumeName, mrmlScene=None, cloneImageData=True):
        """ Clone a scalar node or a labelmap and add it to the scene.
        If no scene is passed, slicer.mrmlScene will be used.
        This method was implemented following the same guidelines as in slicer.modules.volumes.logic().CloneVolume(),
        but it is also valid for labelmap nodes
        :param volumeNode: original node
        :param copyVolumeName: desired name of the labelmap (with a suffix if a node with that name already exists in the scene)
        :param mrmlScene: slicer.mrmlScene by default
        :param cloneImageData: clone also the vtkImageData node
        :return:
        """
        scene = slicer.mrmlScene if mrmlScene is None else mrmlScene

        # Clone DisplayNode
        displayNode = volumeNode.GetDisplayNode()
        displayNodeCopy = None
        if displayNode is not None:
            displayNodeCopy = slicer.mrmlScene.CreateNodeByClass(displayNode.GetClassName())
            displayNodeCopy.CopyWithScene(displayNode)
            scene.AddNode(displayNodeCopy)

        # Clone volumeNode
        clonedVolume = slicer.mrmlScene.CreateNodeByClass(volumeNode.GetClassName())
        clonedVolume.CopyWithScene(volumeNode)

        clonedVolume.SetName(scene.GetUniqueNameByString(copyVolumeName))
        if displayNodeCopy is not None:
            clonedVolume.SetAndObserveDisplayNodeID(displayNodeCopy.GetID())
        else:
            clonedVolume.SetAndObserveDisplayNodeID(None)

        # Clone imageData
        if cloneImageData:
            imageData = volumeNode.GetImageData()
            if imageData is not None:
                clonedImageData = vtk.vtkImageData()
                clonedImageData.DeepCopy(imageData)
                clonedVolume.SetAndObserveImageData(clonedImageData)
            else:
                clonedVolume.SetAndObserveImageData(None)

        # Return result
        scene.AddNode(clonedVolume)
        return clonedVolume