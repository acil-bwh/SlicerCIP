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
 
