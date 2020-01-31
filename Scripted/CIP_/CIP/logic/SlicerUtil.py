'''
Created on Feb 17, 2015
@author: Jorge Onieva
Common functions that can be useful in any Slicer module development
'''

import os
import os.path as path
import logging
from __main__ import slicer, vtk, qt
from . import Util


class SlicerUtil:
    #######################################
    #### Constants / Properties
    #######################################
    try:
        IsDevelopment = slicer.app.settings().value('Developer/DeveloperMode').lower() == 'true'
    except:
        IsDevelopment = False

    CIP_MODULE_ROOT_DIR = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../..')

    CIP_LIBRARY_ROOT_DIR = os.path.join(CIP_MODULE_ROOT_DIR, 'CIP')

    CIP_RESOURCES_DIR = os.path.join(CIP_LIBRARY_ROOT_DIR, 'ui', 'Resources')
    CIP_ICON_DIR = os.path.join(CIP_RESOURCES_DIR, 'Icons')

    ACIL_AcknowledgementText = """This work is funded by the National Heart, Lung, And Blood Institute of the National Institutes of Health under Award Number R01HL116931. 
        The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health."""

    CIP_ModulesCategory = ["Chest Imaging Platform"]
    CIP_ModuleName = "CIP_"

    GIT_REPO_FOLDER = path.join(slicer.app.temporaryPath, 'CIP-Repo')
    GIT_REMOTE_URL = "https://github.com/acil-bwh/SlicerCIP.git"

    ACIL_LOGO_PATH = os.path.join(CIP_ICON_DIR, 'ACIL.png')

    # Aligment
    ALIGNMENT_HORIZONTAL_LEFT = 0x0001
    ALIGNMENT_HORIZONTAL_RIGHT = 0x0002
    ALIGNMENT_HORIZONTAL_CENTER = 0x0004
    ALIGNMENT_HORIZONTAL_JUSTIFY = 0x0008

    ALIGNMENT_VERTICAL_TOP = 0x0020
    ALIGNMENT_VERTICAL_BOTTOM = 0x0040
    ALIGNMENT_VERTICAL_CENTER = 0x0080

    # Preferred window selection order
    preferredWidgetKeysOrder = ("Red", "Yellow", "Green")


    #######################################
    #### Environment internals
    #######################################
    @staticmethod
    def getModuleFolder(moduleName):
        '''Get the folder where a python scripted module is physically stored'''
        path = os.path.dirname(slicer.util.getModule(moduleName).path)
        if (os.sys.platform == "win32"):
            path = path.replace("/", "\\")
        return path

    @staticmethod
    def getSettingsDataFolder(moduleName=""):
        """ Get the full path file where the settings of a module are going to be stored.
        It creates the directory if it doesn't exist.
        For instante, the root base dir in Mac is /Users/jonieva/.config/www.na-mic.org/CIP/ModuleName
        :param moduleName: name of the module (optional)
        :return: full path to the file
        """
        # return os.path.join(os.path.expanduser('~'), "SlicerCIP_Data", moduleName, "Results")
        # p = path.join(path.dirname(slicer.app.slicerDefaultSettingsFilePath), "DataStore", "CIP", moduleName)
        baseDir = os.path.dirname(slicer.app.slicerRevisionUserSettingsFilePath)
        p = path.join(baseDir, "CIP", moduleName)

        if not path.exists(p):
            os.makedirs(p)
            print(("Created path {} for module {} settings".format(p, moduleName)))
        return p

    @staticmethod
    def modulesDbPath():
        """
        Return the full path to the sqlite database that will store the information of all the modules
        :return: full path
        """
        return os.path.join(SlicerUtil.getSettingsDataFolder(), "CIP.db")

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
            return setting  # The setting was already initialized

        if settingDefaultValue is not None:
            slicer.app.settings().setValue(settingPath, settingDefaultValue)

        return settingDefaultValue

    @staticmethod
    def testingDataRootUrl():
        """ Root data where all the images for testing will be stored
        """
        return "http://midas.chestimagingplatform.org/download/item/"

    @staticmethod
    def isSlicerACILLoaded():
        """ Check the existence of the common ACIL module
        :return: True if the module is found
        """
        try:
            m = slicer.modules.acil_
        except:
            return False
        return True

    @staticmethod
    def logDevelop(message, includePythonConsole=False):
        """ Log a message when we Slicer is in Development mode.
        If includePythonConsole, also prints
        @param message:
        """
        if SlicerUtil.IsDevelopment:
            logging.debug(message)
            if includePythonConsole:
                print(message)

    #######################################
    #### Volumes
    #######################################
    @staticmethod
    def setActiveVolumeIds(volumeId, labelmapId=None):
        """
        Display the volume and labelmap specified
        :param volumeId:
        :param labelmapId:
        :return:
        """
        SlicerUtil.displayBackgroundVolume(volumeId)
        SlicerUtil.displayLabelmapVolume(labelmapId)
        # selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        # if volumeId is not None and volumeId != "":
        #     selectionNode.SetReferenceActiveVolumeID(volumeId)
        # if labelmapId is not None and labelmapId != "":
        #     selectionNode.SetReferenceActiveLabelVolumeID(labelmapId)
        #slicer.app.applicationLogic().PropagateVolumeSelection(0)      # This line stopped working in Slicer 4.6

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
        # vlogic = slicer.modules.volumes.logic()
        # resultVolume = vlogic.CloneVolume(bigVolume, smallVolume.GetName() + "_extended")
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
        npb[z0:z1, y0:y1, x0:x1] = nps[:, :, :]
        # Refresh values in mrml
        resultVolume.GetImageData().Modified()
        # Return the result volume
        return resultVolume

    @staticmethod
    def cloneVolume(volumeNode, copyVolumeName, mrmlScene=None, cloneImageData=True, addToScene=True):
        """ Clone a scalar node or a labelmap and add it to the scene.
        If no scene is passed, slicer.mrmlScene will be used.
        This method was implemented following the same guidelines as in slicer.modules.volumes.logic().CloneVolume(),
        but it is also valid for labelmap nodes
        :param volumeNode: original node
        :param copyVolumeName: desired name of the labelmap (with a suffix if a node with that name already exists in the scene)
        :param mrmlScene: slicer.mrmlScene by default
        :param cloneImageData: clone also the vtkImageData node
        :param addToScene: add the cloned volume to the scene (default: True)
        :return: cloned volume
        """
        scene = slicer.mrmlScene if mrmlScene is None else mrmlScene

        # Clone DisplayNode
        displayNode = volumeNode.GetDisplayNode()
        displayNodeCopy = None
        if displayNode is not None:
            displayNodeCopy = scene.CreateNodeByClass(displayNode.GetClassName())
            displayNodeCopy.CopyWithScene(displayNode)
            scene.AddNode(displayNodeCopy)

        # Clone volumeNode
        clonedVolume = scene.CreateNodeByClass(volumeNode.GetClassName())
        clonedVolume.CopyWithScene(volumeNode)

        # clonedVolume.SetName(scene.GetUniqueNameByString(copyVolumeName))
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
        if addToScene:
            scene.AddNode(clonedVolume)
        return clonedVolume

    # @staticmethod
    # def createVolumeFromScratch(volumeName, imageSize, imageSpacing, isLabelmap=False):
    #     # imageSize = [512, 512, 512]
    #     # imageSpacing = [1.0, 1.0, 1.0]
    #     voxelType = vtk.VTK_UNSIGNED_INT if isLabelmap else vtk.VTK_INT
    #     # Create an empty image volume
    #     imageData = vtk.vtkImageData()
    #     imageData.SetDimensions(imageSize)
    #     imageData.AllocateScalars(voxelType, 1)
    #     thresholder = vtk.vtkImageThreshold()
    #     thresholder.SetInputData(imageData)
    #     thresholder.SetInValue(0)
    #     thresholder.SetOutValue(0)
    #     # Create volume node
    #     volumeNode = slicer.vtkMRMLScalarVolumeNode()
    #     volumeNode.SetName(volumeName)
    #     volumeNode.SetSpacing(imageSpacing)
    #     volumeNode.SetImageDataConnection(thresholder.GetOutputPort())
    #     # Add volume to scene
    #     slicer.mrmlScene.AddNode(volumeNode)
    #     displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
    #     slicer.mrmlScene.AddNode(displayNode)
    #     colorNode = SlicerUtil.getNode('vtkMRMLColorTableNodeLabels') if isLabelmap else SlicerUtil.getNode('vtkMRMLColorTableNodeGrey')
    #     displayNode.SetAndObserveColorNodeID(colorNode.GetID())
    #     volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    #     volumeNode.CreateDefaultStorageNode()
    #     return volumeNode

    @staticmethod
    def getLabelmapFromScalar(vtkMRMLScalarVolumeNode, nodeName=""):
        """ Convert a vtkMRMLScalarVolumeNode node in an equivalent vtkMRMLLabelMapVolumeNode
        :param vtkMRMLScalarVolumeNode:
        :param nodeName: name of the result node (default: scalarNodeName_lm)
        :return: vtkMRMLLabelMapVolumeNode
        """
        logic = slicer.modules.volumes.logic()
        if not nodeName:
            nodeName = vtkMRMLScalarVolumeNode.GetName() + "_labelmap"

        node = logic.CreateAndAddLabelVolume(vtkMRMLScalarVolumeNode, nodeName)
        # Make sure that the node name is correct, because sometimes the scene adds a suffix
        node.SetName(nodeName)
        return node


    @staticmethod
    def getFirstActiveVolumeId():
        """
        Return the first active volume id in a visible window (following SlicerUtil.preferredWidgetKeysOrder)
        @return: volume id or None if there is no active volume
        """
        lm = slicer.app.layoutManager()
        if lm is None:
            return None
        for slice in SlicerUtil.preferredWidgetKeysOrder:
            widget = lm.sliceWidget(slice)
            if widget.visible:
                volumeId = SlicerUtil.getActiveVolumeIdInSlice(slice)
                if volumeId:
                    return volumeId
        return None

    @staticmethod
    def getFirstActiveLabelmapId():
        """
        Return the first active labelmap id (searching in Red, Yellow and Green windows)
        @return: labelmap id or None if there is no active labelmap
        """
        lm = slicer.app.layoutManager()
        for slice in SlicerUtil.preferredWidgetKeysOrder:
            widget = lm.sliceWidget(slice)
            if widget.visible:
                volumeId = SlicerUtil.getActiveLabelmapIdInSlice(slice)
                if volumeId:
                    SlicerUtil.logDevelop("Found active labelmap {} in slice {}".format(volumeId, slice), includePythonConsole=True)
                    return volumeId
        return None


    @staticmethod
    def getActiveVolumeIdInSlice(sliceName):
        """ Get the active volume in a 2D Slice (background if possible, foreground otherwise)
        :param sliceName: typically "Red", "Green" or "Yellow"
        :return: volume node id or None
        """
        layoutManager = slicer.app.layoutManager()
        compositeNode = layoutManager.sliceWidget(sliceName).mrmlSliceCompositeNode()
        node = compositeNode.GetBackgroundVolumeID()
        if node is not None:
            return node
        # If background is None, try foreground
        node = compositeNode.GetForegroundVolumeID()
        return node

    @staticmethod
    def getActiveLabelmapIdInSlice(sliceName):
        """ Get the active labelmap in a 2D Slice
        :param sliceName: typically "Red", "Green" or "Yellow"
        :return: labelmap node id or None
        """
        layoutManager = slicer.app.layoutManager()
        compositeNode = layoutManager.sliceWidget(sliceName).mrmlSliceCompositeNode()
        return compositeNode.GetLabelVolumeID()

    @staticmethod
    def getActiveVolumeIdInRedSlice():
        """ Get the active volume in the Red Slice (background if possible, foreground otherwise)
        :return: volume node id or None
        """
        return SlicerUtil.getActiveVolumeIdInSlice("Red")

    @staticmethod
    def getFirstScalarNode():
        """ Get the first vtkMRMLScalarVolumeNode in the scene
        :return: node or None
        """
        nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLScalarVolumeNode")
        nodes.UnRegister(nodes)
        if nodes.GetNumberOfItems() > 0:
            return nodes.GetItemAsObject(0)
        return None

    @staticmethod
    def getFirstLabelmapNode():
        """ Get the first vtkMRMLLabelMapVolumeNode in the scene
        :return: node or None
        """
        nodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLLabelMapVolumeNode")
        nodes.UnRegister(nodes)
        if nodes.GetNumberOfItems() > 0:
            return nodes.GetItemAsObject(0)
        return None

    @staticmethod
    def getNode(nodeNameOrID):
        """
        Get a node given name. None if it doesn't exist.
        Developed to fix backwards compatibility broken in Slicer
        :param nodeName: str. Name or id of the node
        :return: node or None
        """
        node = slicer.mrmlScene.GetNodeByID(nodeNameOrID)
        if node:
            return node
        nodes = slicer.util.getNodes(nodeNameOrID)
        if len(nodes) == 0:
            return None
        return nodes[nodeNameOrID]

    @staticmethod
    def getNodes(nodeMask):
        """
        Get a list of nodes given a name mask.
        Developed to fix backwards compatibility broken in Slicer
        :param nodeName: str. "Mask" of the node
        :return: nodeMask or None
        """
        nodes = slicer.util.getNodes(nodeMask)
        return list(nodes.keys())


    @staticmethod
    def isOtherVolumeVisible(volumeId):
        """
        Check if there is a background volume visible in ANY of the VISIBLE slice widgets (Red, Yellow, Green) that is
        different from the specified
        :param volumeId:
        :return: True if there is any volume visible that is not the passed one
        """
        layoutManager = slicer.app.layoutManager()
        for slice in layoutManager.sliceViewNames():
            if layoutManager.sliceWidget(slice).visible and SlicerUtil.getActiveVolumeIdInSlice(slice) != volumeId:
                return True
        return False

    @staticmethod
    def filterVolumeName(name):
        """ Remove the suffixes that Slicer could introduce in a volume name (ex: myVolume_1)
        @param name: current name in Slicer
        @return: name without suffixes
        """
        import re
        expr = "^(.*)(_\d+)$"
        m = re.search(expr, name)
        if m:
            # There is suffix. Remove
            suffix = m.groups(0)[1]
            return name.replace(suffix, "")
        # No suffix
        return name

    @staticmethod
    def getCaseNameFromLabelmap(labelmap_name):
        """ Get the case name from a labelmap
        @param labelmap_name:
        @return: case name
        """
        name = SlicerUtil.filterVolumeName(labelmap_name)
        return Util.get_case_name_from_labelmap(name)

    @staticmethod
    def getNodesByClass(className, includeSubclasses=False):
        """
        Get a list with all the "className" nodes available in the scene.
        Just a more convenient way of using the GetNodesByClass method
        @param className: name of the class
        @param includeSubclasses: include also the subclasses
        @return:
        """
        l = []
        col = slicer.mrmlScene.GetNodesByClass(className)
        for i in range(col.GetNumberOfItems()):
            item = col.GetItemAsObject(i)
            if includeSubclasses:
                # Always append (subclasses included)
                l.append(item)
            else:
                # Make sure that the node is not a subclass
                if item.GetClassName() == className:
                    l.append(item)
        return l

    @staticmethod
    def isExtensionMatch(labelmapNode, key):
        """ Check if a labelmap node meets one of the ACIL given labelmap conventions
        @param labelmapNode:
        @param key: convention key (see Util.file_conventions_extensions)
        @return: Bool
        """
        name = SlicerUtil.filterVolumeName(labelmapNode.GetName())
        lmExt = name.split('_')[-1]
        ext = Util.file_conventions_extensions[key].split('.')[0]
        return ext == ("_" + lmExt)

    @staticmethod
    def clearVolume(volumeNode):
        slicer.modules.volumes.logic().ClearVolumeImageData(volumeNode)

    #######################################
    #### Fiducials
    #######################################
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
        # f = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
        # f.GetMarkupPointVector(0,0) --> returns a vtkVector3d with the coordinates for the
        # first node where the fidual is displayed (param 0) and the number of markup (param1)

    @staticmethod
    def getRootAnnotationsNode():
        """ Get the root annotations node global to the scene, creating it if necessary.
        This is useful as a starting point to add rulers to the scene
        :return: "All Annotations" vtkMRMLAnnotationHierarchyNode
        """
        annotationsLogic = slicer.modules.annotations.logic()
        rootHierarchyNodeId = annotationsLogic.GetTopLevelHierarchyNodeID()
        return slicer.util.getNode(rootHierarchyNodeId)

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
        # selectionNode = applicationLogic.GetSelectionNode()
        # selectionNode.SetReferenceActivePlaceNodeClassName(fiducialClass)
        interactionNode = applicationLogic.GetInteractionNode()
        if isFiducialsMode:
            if keepFiducialsModeOn:
                interactionNode.SwitchToPersistentPlaceMode()
            else:
                interactionNode.SwitchToSinglePlaceMode()
        else:
            interactionNode.SwitchToViewTransformMode()

    @staticmethod
    def setFiducialsCursorMode(isFiducialsMode, keepFiducialsModeOn=False):
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
    def setCrosshairCursor(isActive):
        """Turn on or off the crosshair and enable navigation mode
        by manipulating the scene's singleton crosshair node.
        :param isActive: enable / disable crosshair (boolean value)
        """
        crosshairNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLCrosshairNode')
        if crosshairNode:
            crosshairNode.SetCrosshairMode(int(isActive))

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

    #######################################
    #### GUI / Layout
    #######################################
    @staticmethod
    def refreshActiveWindows():
        """ Refresh all the windows currently visible to the user"""
        slicer.app.processEvents()
        lm = slicer.app.layoutManager()
        for windowName in lm.sliceViewNames():
            slice = lm.sliceWidget(windowName)
            if not slice.isHidden():
                slice.repaint()

    @staticmethod
    def getIcon(iconName, isSystemIcon=False):
        """ Build a new QIcon from the common CIP icons library or from the Slicer system icons
        :param iconName: name of the file (ex: previous.png)
        :param isSystemIcon: True if the icon belongs to the Slicer library. The available files can be found in the
        folder "/Users/Jorge/Projects/BWH/Slicer/Libs/MRML/Widgets/Resources/Icons".
        isSystemIcon=False for CIP icons (in "SlicerCIP/Scripted/CIP_/CIP/ui/Resources/Icons/")
        :return: QIcon object
        """
        if not isSystemIcon:
            return qt.QIcon(os.path.join(SlicerUtil.CIP_ICON_DIR, iconName))
        return qt.QIcon(":/Icons/" + iconName)

    @staticmethod
    def changeLayout(layoutNumber):
        """ Change the general layout in Slicer
        :param layoutNumber: layout id number
        """
        applicationLogic = slicer.app.applicationLogic()
        interactionNode = applicationLogic.GetInteractionNode()
        # Change in signature in Reset method.
        try:
            interactionNode.Reset(None)
        except:
            # Backwards compatibility
            interactionNode.Reset()
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(layoutNumber)
        # Call this function to force the refresh of properties like the field of view of the sliceNodes
        slicer.app.processEvents()

    @staticmethod
    def changeLayoutToAxial():
        SlicerUtil.changeLayout(6)

    @staticmethod
    def changeLayoutToSagittal():
        SlicerUtil.changeLayout(7)

    @staticmethod
    def changeLayoutToCoronal():
        SlicerUtil.changeLayout(8)

    @staticmethod
    def changeContrastWindow(window, level):
        """ Adjust the window contrast level in the range min-max.
        Note: it takes the first visible node in 2D windows
        :param window: size of the window
        :param level: center of the window
        """
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            v = compNode.GetBackgroundVolumeID()
            if v is not None and v != "":
                displayNode = slicer.mrmlScene.GetNodeByID(v).GetDisplayNode()
                displayNode.AutoWindowLevelOff()
                displayNode.SetWindow(window)
                displayNode.SetLevel(level)
                return

    @staticmethod
    def jumpToSlice(widgetName, slice):
        """ Jump one of the three 2D windows to a number of slice.
        :param widgetName: "Red", "Yellow" or "Green"
        :param slice: number of slice (RAS coords)
        """
        layoutManager = slicer.app.layoutManager()
        widget = layoutManager.sliceWidget(widgetName)
        widgetSliceNode = widget.sliceLogic().GetLabelLayer().GetSliceNode()
        if widgetName == "Red":
            widgetSliceNode.JumpSlice(0, 0, slice)
        elif widgetName == "Yellow":
            widgetSliceNode.JumpSlice(slice, 0, 0)
        elif widgetName == "Green":
            widgetSliceNode.JumpSlice(0, slice, 0)

    @staticmethod
    def jumpToSeed(coords):
        """ Position all the 2D windows in a RAS coordinate, and also centers the windows around
        :param coord: array/list/tuple that contains a RAS coordinate
        """
        sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
        for sliceNode in sliceNodes.values():
            sliceNode.JumpSliceByCentering(coords[0], coords[1], coords[2])

    @staticmethod
    def centerAllVolumes():
        """ Center all the volumes that are currently visible in the 2D Windows
        """
        lm = slicer.app.layoutManager()
        for sliceView in lm.sliceViewNames():
            lm.sliceWidget(sliceView).sliceLogic().FitSliceToAll()

    @staticmethod
    def displayBackgroundVolume(volumeNodeId):
        """
        Set an active scalar volume in the background
        :param volumeNodeId:
        """
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetBackgroundVolumeID(volumeNodeId)

    @staticmethod
    def displayForegroundVolume(volumeNodeId, opacity=1.0):
        """ Display a scalar or a labelmap in all the 2D windows as Foreground with an optional opacity
        :param volumeNodeId: scalar node or labelmap id
        :param opacity: 0.0-1.0 value
        """
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetForegroundVolumeID(volumeNodeId)
            compNode.SetForegroundOpacity(opacity)

    @staticmethod
    def displayLabelmapVolume(labelmapNodeId):
        """ Display a labelmap in all the 2D windows with an optional opacity
        :param volumeNodeId: labelmap id
        """
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLabelVolumeID(labelmapNodeId)


    @staticmethod
    def changeLabelmapOpacity(opacity):
        """ Change the labelmap opacity in all the 2D windows
        @param opacity:
        @return:
        """
        compNodes = slicer.util.getNodes("vtkMRMLSliceCompositeNode*")
        for compNode in compNodes.values():
            compNode.SetLabelOpacity(opacity)

    @staticmethod
    def getLabelmapOpacity():
        """ Get the current labelmap opacity using the first visible compositeNode following SlicerUtil.preferredWidgetKeysOrder
        @return:
            Labelmap opacity of the first visible compositeNode or None if there is any unexpected problem
        """
        try:
            lm = slicer.app.layoutManager()
            for slice in SlicerUtil.preferredWidgetKeysOrder:
                widget = lm.sliceWidget(slice)
                if widget.visible:
                    return widget.mrmlSliceCompositeNode().GetLabelOpacity()
            return None
        except:
            return None
    @staticmethod
    def is3DViewVisible():
        """
        True if there is at least a 3D view currently visible
        @return: Boolean
        """
        lm = slicer.app.layoutManager()
        if lm.threeDViewCount == 0:
            return False
        return lm.threeDWidget(0).visible

    @staticmethod
    def takeSnapshot(fullFileName, type=-1, hideAnnotations=False):
        """ Save a png snapshot of the specified window
        :param fullFileName: Full path name of the output file (ex: "/Data/output.png")
        :param type: slicer.qMRMLScreenShotDialog.FullLayout, slicer.qMRMLScreenShotDialog.ThreeD,
                    slicer.qMRMLScreenShotDialog.Red, slicer.qMRMLScreenShotDialog.Yellow, slicer.qMRMLScreenShotDialog.Green
                    Default: main window
        :param hideAnnotations: bool. Remove the volume/labelmap name labels
        :return: full path of the snapshot
        """
        # show the message even if not taking a screen shot
        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly

        if hideAnnotations:
            # Hide volume name
            SlicerUtil.showCornerAnnotations(False)

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        # Save as a png file
        qpixMap.save(fullFileName)
        if hideAnnotations:
            SlicerUtil.showCornerAnnotations(True)
        return fullFileName

    @staticmethod
    def showCornerAnnotations(show):
        """
        Show/Hide the volume/labelmap names in all the slice view windows
        :param show: bool. Show/hide the annotations
        """
        lm = slicer.app.layoutManager()
        for key in lm.sliceViewNames():
            sliceView = lm.sliceWidget(key).sliceView()
            sliceView.cornerAnnotation().SetVisibility(show)
            sliceView.scheduleRender()

    @staticmethod
    def showToolbars(show):
        """ Show/hide all the superior toolbars in the Slicer GUI
        @param show:
        """
        for toolbar in slicer.util.mainWindow().findChildren('QToolBar'):
            toolbar.setVisible(show)

    @staticmethod
    def createNewColormapNode(nodeName, numberOfColors=0):
        """ Create a new empty color map node
        @param nodeName: name of the node to be created
        @param numberOfColors: total number of colors of the color node (it can be set later)
        @return: new node
        """
        colorNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLColorTableNode")
        slicer.mrmlScene.AddNode(colorNode)
        colorNode.SetName(nodeName)
        colorNode.SetTypeToUser()
        colorNode.NamesInitialisedOn()
        colorNode.SetNumberOfColors(numberOfColors)
        return colorNode

    @staticmethod
    def getInteractor(sliceNodeID):
        """
        Get the interactor for a slice node
        @param sliceNodeID: str. SliceNode id
        @return: vtkRenderWindowInteractor object
        """
        layoutManager = slicer.app.layoutManager()
        try:
            sliceNode = slicer.mrmlScene.GetNodeByID(sliceNodeID)
            return layoutManager.sliceWidget(sliceNode.GetLayoutName()).sliceView().interactor()
        except:
            logging.warning("Iterator for {} could not be obtained".format(sliceNodeID))
            return None

    #######################################
    #### Testing
    #######################################
    @staticmethod
    def downloadVolumeForTests(downloadWhenCached=False, tryUsingACILNavigator=True, widget=None):
        """ Download a sample volume for testing purposes.
        The first option will be to use the ACIL caseNavigatorWidget (unless tryUsingACILNavigator==False).
        Otherwise, it will download the CT chest scan in http://www.slicer.org/slicerWiki/images/3/31/CT-chest.nrrd
        @param downloadWhenCached: download the case even if it's been previously downloaded
        @param tryUsingACILNavigator: try to use case the ACIL case navigator as the primary source for data
        @param widget: Parent widget where the navigator could be included
        @return: loaded volume
        """
        volume = None
        if tryUsingACILNavigator and SlicerUtil.isSlicerACILLoaded():
            try:
                logging.info("Trying to use the case navigator to download the case...")
                # Try first with case navigator (not necessarily included!)
                downloadButton = slicer.util.findChildren(widget, "downloadSingleCaseButton")[0]
                caseIdTxt = slicer.util.findChildren(widget, "singleCaseIdTxt")[0]
                studyButton = slicer.util.findChildren(widget, "studyIdButton_COPDGene")[0]
                studyButton.click()
                caseId = "11488P_INSP_STD_HAR_COPD"
                caseIdTxt.setText(caseId)
                if downloadWhenCached:
                    # Disable cache to always force the download
                    cbCache = slicer.util.findChildren(widget, "cbCacheMode")[0]
                    cbCache.setChecked(False)
                downloadButton.click()
                volume = SlicerUtil.getNode(caseId)
            except Exception as ex:
                logging.info("Case Navigator failed ({0}). Downloading web case...".format(ex.message))
        if volume is None:
            # Load the volume from a Slicer generic testing cases url
            import urllib.request, urllib.parse, urllib.error
            url = "http://www.slicer.org/slicerWiki/images/3/31/CT-chest.nrrd"
            name = url.split("/")[-1]
            localFilePath = os.path.join(slicer.app.temporaryPath, name)
            if not os.path.exists(localFilePath) or os.stat(localFilePath).st_size == 0 or downloadWhenCached:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.request.urlretrieve(url, localFilePath)
            logging.debug("Loading volume in {0}...".format(localFilePath))
            (loaded, volume) = slicer.util.loadVolume(localFilePath, returnNode=True)
        return volume

    ### Methods to find widgets that should be merged into Base/Python/slicer/Util.py at some point (Pull Request made)
    @staticmethod
    def findChildren(widget=None, name="", text="", title="", className=""):
        """ Return a list of child widgets that meet all the given criteria.
        If no criteria are given, the function will return all the child widgets.
        The function applies an "and" filter, instead of the previous "or" behavior
        (see http://slicer-devel.65872.n3.nabble.com/Changing-the-behavior-of-slicer-util-findChildren-td4036266.html
        for additional info)
        :param widget: parent widget where the widgets will be searched
        :param name: name attribute of the widget
        :param text: text attribute of the widget
        :param title: title attribute of the widget
        :param className: className() attribute of the widget
        :return: list with all the widgets that meet all the given criteria.
        """
        # TODO: figure out why the native QWidget.findChildren method does not seem to work from PythonQt
        import slicer, fnmatch
        if not widget:
            widget = slicer.util.mainWindow()
        if not widget:
            return []
        children = []
        parents = [widget]
        while parents:
            p = parents.pop()
            # sometimes, p is null, f.e. when using --python-script or --python-code
            if not p:
                break
            if not hasattr(p, 'children'):
                continue
            parents += p.children()
            matched_filter_criteria = True
            if name and hasattr(p, 'name'):
                matched_filter_criteria &= fnmatch.fnmatchcase(p.name, name)
            if text and hasattr(p, 'text'):
                matched_filter_criteria &= fnmatch.fnmatchcase(p.text, text)
            if title and hasattr(p, 'title'):
                matched_filter_criteria &= fnmatch.fnmatchcase(p.title, title)
            if className and hasattr(p, 'className'):
                matched_filter_criteria &= fnmatch.fnmatchcase(p.className(), className)

            if matched_filter_criteria:
                children.append(p)
        return children

    @staticmethod
    def findChild(widget=None, name="", text="", title="", className=""):
        """ Return a single child widget that meet all the given criteria.
        If there is more than one widget that matches the conditions, an Exception is raised.
        If there is no widget that matches the conditions, the method returns None.
        :param widget: parent widget where the widgets will be searched
        :param name: name attribute of the widget
        :param text: text attribute of the widget
        :param title: title attribute of the widget
        :param className: className() attribute of the widget
        :return: single widget that meet all the given criteria (or None otherwise)
        """
        results = SlicerUtil.findChildren(widget, name, text, title, className)
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise Exception("There is more than one widget that matches the given conditions")
        return results[0]

