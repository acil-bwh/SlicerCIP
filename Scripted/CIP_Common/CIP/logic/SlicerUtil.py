'''
Created on Feb 17, 2015
@author: Jorge Onieva
Common functions that can be useful in any Slicer module development
'''

from __main__ import slicer
import os


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

    RESOURCES_DIR = os.path.join(CIP_LIBRARY_ROOT_DIR, 'ui', 'Resources')
    ICON_DIR = os.path.join(RESOURCES_DIR, 'Icons')
        
    ACIL_AcknowledgementText = """This work is funded by the National Heart, Lung, And Blood Institute of the National Institutes of Health under Award Number R01HL116931. 
        The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health."""

    CIP_ModulesCategory = ["Chest Imaging Platform.Modules"]
    CIP_ModuleName = "CIP_Common"

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
    def is_SlicerACIL_loaded():
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
    def setActiveVolume(volumeId, labelmapId=None):
        selectionNode = slicer.app.applicationLogic().GetSelectionNode()
        if volumeId is not None and volumeId != "":
            selectionNode.SetReferenceActiveVolumeID(volumeId)
        if labelmapId is not None and labelmapId != "":
            selectionNode.SetReferenceActiveLabelVolumeID(labelmapId)
        slicer.app.applicationLogic().PropagateVolumeSelection(0)



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