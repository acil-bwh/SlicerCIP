'''
Created on Feb 17, 2015
@author: Jorge Onieva
Common functions that can be useful in any Slicer module development
'''

from __main__ import slicer, vtk
import os

from . import Util

class SlicerUtil:
    # Constants    
    try:
        IsDevelopment = slicer.app.settings().value('Developer/DeveloperMode').lower() == 'true'
    except:
        IsDevelopment = False


    CIP_MODULE_ROOT_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../..')
    #CIP_GIT_REPO_FOLDER = os.path.realpath(CIP_MODULE_ROOT_DIR + '/../CIP-Repo')
    CIP_DEFAULT_GIT_REPO_FOLDER = os.path.join(slicer.app.temporaryPath, 'CIP-Repo')
    CIP_GIT_REMOTE_URL = "https://acilgeneric:bwhacil2015@github.com/acil-bwh/ACILSlicer.git"
    CIP_LIBRARY_ROOT_DIR = os.path.join(CIP_MODULE_ROOT_DIR, 'CIP')

    CIP_RESOURCES_DIR = os.path.join(CIP_LIBRARY_ROOT_DIR, 'ui', 'Resources')
    CIP_ICON_DIR = os.path.join(CIP_RESOURCES_DIR, 'Icons')
        
    ACIL_AcknowledgementText = """This work is funded by the National Heart, Lung, And Blood Institute of the National Institutes of Health under Award Number R01HL116931. 
        The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health."""

    CIP_ModulesCategory = ["Chest Imaging Platform.Modules"]
    CIP_ModuleName = "CIP_Common"

    # Aligment
    ALIGNMENT_HORIZONTAL_LEFT = 0x0001
    ALIGNMENT_HORIZONTAL_RIGHT = 0x0002
    ALIGNMENT_HORIZONTAL_CENTER = 0x0004
    ALIGNMENT_HORIZONTAL_JUSTIFY = 0x0008

    ALIGNMENT_VERTICAL_TOP = 0x0020
    ALIGNMENT_VERTICAL_BOTTOM = 0x0040
    ALIGNMENT_VERTICAL_CENTER = 0x0080


    @staticmethod
    def getModuleFolder(moduleName):
        '''Get the folder where a python scripted module is physically stored''' 
        path = os.path.dirname(slicer.util.getModule(moduleName).path)
        if (os.sys.platform == "win32"):
            path = path.replace("/", "\\")
        return path
 
    @staticmethod
    def setSetting(moduleName, settingName, settingValue):
        '''Set the value of a setting in Slicer'''
        settingPath = "%s/%s" % (moduleName, settingName)     
        slicer.app.settings().setValue(settingPath, settingValue)
     
 
    @staticmethod
    def settingGetOrSetDefault(moduleName, settingName, settingDefaultValue=None):
        '''Try to find the value of a setting in Slicer and, if it does not exist, set it to the settingDefaultValue (optional)'''
        settingPath = "%s/%s" % (moduleName, settingName)
        setting = slicer.app.settings().value(settingPath)
        if setting is not None:
            return setting    # The setting was already initialized
        
        if settingDefaultValue is not None:
            slicer.app.settings().setValue(settingPath, settingDefaultValue)
                
        return settingDefaultValue
    
    @staticmethod     
    def createNewFiducial(x, y, z, radX, radY, radZ, scalarNode):
        '''Create a new fiducial (ROI) that will be visible in the scalar node passed.
        Parameters: 
        - x, y, z: fiducial coordinates
        - radX, radY, radZ: ROI size
        - scalarNode: vtk scalar node where the fiducial will be displayed'''
        fiducial = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationROINode')
        fiducial.SetXYZ(x, y, z)
        fiducial.SetRadiusXYZ(radX, radY, radZ)
        # Add the fiducial to the scalar node
        displayNodeID = scalarNode.GetDisplayNode().GetID()
        fiducial.AddAndObserveDisplayNodeID(displayNodeID)
        # Get fiducial (Point)
        #f = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
        #f.GetMarkupPointVector(0,0) --> returns a vtkVector3d with the coordinates for the
        # first node where the fidual is displayed (param 0) and the number of markup (param1)

    @staticmethod
    def refreshActiveWindows():
        """ Refresh all the windows currently visible to the user"""
        lm = slicer.app.layoutManager()
        for windowName in lm.sliceViewNames():
            slice = lm.sliceWidget(windowName)
            if not slice.isHidden():
                slice.repaint()

    @staticmethod
    def isSlicerACILLoaded():
        """ Check the existence of the common ACIL module
        :return: True if the module is found
        """
        try:
            m = slicer.modules.acil_common
        except:
            return False
        return True

    @staticmethod
    def getRootAnnotationsNode():
        """ Get the root annotations node global to the scene, creating it if necessary.
        This is useful as a starting point to add rulers to the scene
        :return: "All Annotations" vtkMRMLAnnotationHierarchyNode
        """
        rootHierarchyNode = slicer.util.getNode('All Annotations')
        if rootHierarchyNode is None:
            # Create root annotations node
            rootHierarchyNode = slicer.modules.annotations.logic().GetActiveHierarchyNode()
        return rootHierarchyNode


    @staticmethod
    def __setMarkupsMode__(isFiducialsMode, fiducialClass, keepFiducialsModeOn):
        """ Activate fiducials mode.
        When activateFiducials==True, the mouse cursor will be ready to add fiducials. Also, if
        keepFiducialsModeOn==True, then the cursor will be still in Fiducials mode until we deactivate it by
        calling setFiducialsMode with activateFiducials=False
        :param isFiducialsMode: True for "fiducials mode". False for a regular use
        :fiducialClass: "vtkMRMLMarkupsFiducialNode", "vtkMRMLAnnotationRulerNode"...
        :param keepFiducialsModeOn: when True, we can add an unlimited number of fiducials. Otherwise after adding the
        first fiducial we will come back to the regular state
        """
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetReferenceActivePlaceNodeClassName(fiducialClass)
        interactionNode = applicationLogic.GetInteractionNode()
        if isFiducialsMode:
            # Mouse cursor --> fiducials
            interactionNode.SetCurrentInteractionMode(1)
            # Persistence depending on if we to keep fiducials (or just one)
            interactionNode.SetPlaceModePersistence(keepFiducialsModeOn)
        else:
            # Regular cursor
            interactionNode.SetCurrentInteractionMode(2)
            interactionNode.SetPlaceModePersistence(False)

    @staticmethod
    def setFiducialsMode(isFiducialsMode, keepFiducialsModeOn=False):
        """ Activate fiducials mode.
        When activateFiducials==True, the mouse cursor will be ready to add fiducials. Also, if
        keepFiducialsModeOn==True, then the cursor will be still in Fiducials mode until we deactivate it by
        calling setFiducialsMode with activateFiducials=False
        :param isFiducialsMode: True for "fiducials mode". False for a regular use
        :param keepFiducialsModeOn: when True, we can add an unlimited number of fiducials. Otherwise after adding the
        first fiducial we will come back to the regular state
        """
        SlicerUtil.__setMarkupsMode__(isFiducialsMode, "vtkMRMLMarkupsFiducialNode", keepFiducialsModeOn)

    @staticmethod
    def setRulersMode(isRulersMode, keepFiducialsModeOn=False):
        """ Activate fiducials ruler mode.
        When activateFiducials==True, the mouse cursor will be ready to add fiducials. Also, if
        keepFiducialsModeOn==True, then the cursor will be still in Fiducials mode until we deactivate it by
        calling setFiducialsMode with activateFiducials=False
        :param isRulersMode: True for "fiducials mode". False for a regular use
        :param keepFiducialsModeOn: when True, we can add an unlimited number of fiducials. Otherwise after adding the
        first fiducial we will come back to the regular state
        """
        SlicerUtil.__setMarkupsMode__(isRulersMode, "vtkMRMLAnnotationRulerNode", keepFiducialsModeOn)


    @staticmethod
    def setActiveVolumeId(volumeId, labelmapId=None):
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        if volumeId is not None and volumeId != "":
            selectionNode.SetReferenceActiveVolumeID(volumeId)
        if labelmapId is not None and labelmapId != "":
            selectionNode.SetReferenceActiveLabelVolumeID(labelmapId)
        slicer.app.applicationLogic().PropagateVolumeSelection(0)

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
        origin = Util.ras_to_ijk(bigVolume, smallVolume.GetOrigin())
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
        :return: cloned volume
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

        #clonedVolume.SetName(scene.GetUniqueNameByString(copyVolumeName))
        clonedVolume.SetName(copyVolumeName)
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
    def getActiveVolumeIdInRedSlice():
        """ Get the active volume in the Red Slice
        :return: volume node id or None
        """
        layoutManager = slicer.app.layoutManager()
        compositeNode = layoutManager.sliceWidget("Red").mrmlSliceCompositeNode()
        backgroundNode = compositeNode.GetBackgroundVolumeID()
        if backgroundNode is not None:
            return backgroundNode
        # If background is None, try foreground
        backgroundNode = compositeNode.GetForegroundVolumeID()
        return backgroundNode


    @staticmethod
    def changeLayout(layoutNumber):
        """ Change the general layout in Slicer
        :param layoutNumber: layout id number
        """
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        interactionNode.Reset()
        interactionNode.SwitchToPersistentPlaceMode()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(layoutNumber)

    @staticmethod
    def vtkImageData_numpy_array(vtkImageData_node):
        """ Return a numpy array from a vtkImageData node
        :param vtkImageData_node:
        :return:
        """
        shape = list(vtkImageData_node.GetDimensions())
        shape.reverse()
        return vtk.util.numpy_support.vtk_to_numpy(vtkImageData_node.GetPointData().GetScalars()).reshape(shape)
        # shape = list(vtk_node.GetImageData().GetDimensions())
        # shape.reverse()
        # arr = vtk.util.numpy_support.vtk_to_numpy(vtk_node.GetPointData().GetScalars()).reshape(shape)
        # spacing = list(vtk_node.GetSpacing())
        # spacing.reverse()
        # origin = list(vtk_node.GetOrigin())
        # origin.reverse()
        # return arr, spacing, origin

    @staticmethod
    def jumpToSlice(widgetName, slice):
        layoutManager = slicer.app.layoutManager()
        widget = layoutManager.sliceWidget(widgetName)
        widgetSliceNode = widget.sliceLogic().GetLabelLayer().GetSliceNode()
        if widgetName == "Red":
            widgetSliceNode.JumpSlice(0, 0, slice)
        elif widgetName == "Yellow":
            widgetSliceNode.JumpSlice(slice, 0, 0)
        elif widgetName == "Green":
            widgetSliceNode.JumpSlice(0, slice, 0)



        # @staticmethod
    # def gitUpdateCIP():
    #     if Util.AUTO_UPDATE_DISABLED:
    #         print("CIP auto update is disabled")
    #         return False
    #
    #     #try:
    #     update = Util.__gitUpdate__()
    #     if update:
    #         # Copy the directory under CIP_GIT_REPO with this module name
    #         #srcPath = "%s/%s" %    (Util.CIP_GIT_REPO_FOLDER, moduleName)
    #         srcPath = Util.CIP_DEFAULT_GIT_REPO_FOLDER
    #         print('src: ', srcPath)
    #         #destPath = os.path.join(Util.CIP_LIBRARY_ROOT_DIR, moduleName)
    #         destPath = os.path.realpath(SlicerUtil.CIP_MODULE_ROOT_DIR + '/..')
    #         print('dest: ', destPath)
    #         # First rename the folder to a temp name, as a backup
    #         backupPath = destPath + "_TMP"
    #         os.rename(destPath, backupPath)
    #         # Copy the folder
    #         shutil.copytree(srcPath, destPath)
    #         # Remove the temp folder
    #         shutil.rmtree(backupPath)
    #
    #     return update
#         except Exception as ex:
#             print (ex.message())
#             return False

    # @staticmethod
    # def __gitUpdate__():
    #     '''Gets the last version of the CIP git repository.
    #     In case it does not exist, it creates it from scratch
    #     Returns true if there was any update in the repository'''
    #     from git import Repo
    #
    #     if os.path.exists(Util.CIP_DEFAULT_GIT_REPO_FOLDER):
    #         # Check for updates
    #         repo = Repo(Util.CIP_DEFAULT_GIT_REPO_FOLDER)
    #         #remote = repo.remotes.pop()
    #         remote = repo.remotes.origin
    #         prevCommit = repo.head.commit.hexsha
    #         status = remote.fetch().pop()
    #         if status and status.commit.hexsha != prevCommit:
    #             remote.pull()
    #             return True
    #
    #         return False
    #
    #     else:
    #         # Create the new repository
    #         os.makedirs(Util.CIP_DEFAULT_GIT_REPO_FOLDER)
    #         os.chmod(Util.CIP_DEFAULT_GIT_REPO_FOLDER, 0777)
    #         #repo = Repo(Util.CIP_GIT_REPO_FOLDER)
    #         Repo.clone_from(Util.CIP_GIT_REMOTE_URL, Util.CIP_DEFAULT_GIT_REPO_FOLDER)
    #         print ("Created folder %s (first time update)" % Util.CIP_DEFAULT_GIT_REPO_FOLDER)
    #         # Always update the first time
    #         return True