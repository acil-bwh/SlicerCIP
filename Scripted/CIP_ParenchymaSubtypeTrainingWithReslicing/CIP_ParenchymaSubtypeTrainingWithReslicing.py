import os, sys
import vtk, qt, ctk, slicer
from shutil import copyfile
import time

from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP.logic import Util
from CIP_ParenchymaSubtypeTraining import *
from CIP.logic import geometry_topology_data as gtd

#
# CIP_ParenchymaSubtypeTrainingWithReslicing
class CIP_ParenchymaSubtypeTrainingWithReslicing(CIP_ParenchymaSubtypeTraining):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training with reslicing"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName, "CIP_ParenchymaSubtypeTraining"]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital"]
        self.parent.helpText = """Training parenchyma subtypes done quickly by an expert after reslicing a volume"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_ParenchymaSubtypeTrainingWithReslicingWidget
#
class CIP_ParenchymaSubtypeTrainingWithReslicingWidget(CIP_ParenchymaSubtypeTrainingWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    @property
    def moduleName(self):
        return "CIP_ParenchymaSubtypeTrainingWithReslicing"

    def __init__(self, parent):
        CIP_ParenchymaSubtypeTrainingWidget.__init__(self, parent)

        # Slicing
        self.sliceMeasurements = [1, 3, 5, 10, 15, 20, 30]  # Slice measurementes (in mm)
        self.customExtension = "MmAirwayCount.xml"

        # Before running the setup, define the additional files
        for id in self.sliceMeasurements:
            self.additionalFileTypes["Airway count ({} mm)".format(id)] = (False, "_{}{}".format(id, self.customExtension))

    def _initLogic_(self):
        """Create a new logic object for the plugin"""
        self.currentReslicedVolume = None
        self.logic = CIP_ParenchymaSubtypeTrainingWithReslicingLogic()

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        CIP_ParenchymaSubtypeTrainingWidget.setup(self)
        self.volumeSelectionLayout.addRow("Slice size:", None)


        self.sliceSelectionRadioButtonGroup = qt.QButtonGroup()
        for id in range(len(self.sliceMeasurements)):
            button = qt.QRadioButton("{} mm".format(self.sliceMeasurements[id]))
            self.sliceSelectionRadioButtonGroup.addButton(button, id)
            self.volumeSelectionLayout.addRow("", button)

        # Add button for reslicing
        self.resliceButton = qt.QPushButton("Reslice")
        self.volumeSelectionLayout.addRow("", self.resliceButton)
        self.resliceButton.connect('clicked()', self.__onResliceButtonClicked__)

        # Select by default the airway type
        self.typesRadioButtonGroup.buttons()[2].setChecked(True)
        self.updateState()

    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        self.blockNodeEvents = False
        SlicerUtil.setFiducialsCursorMode(True, True)
        #
        # if self.currentVolumeLoaded:
        #     SlicerUtil.setActiveVolumeIds(self.volumeSelector.currentNodeId)
        #     self.currentVolumeLoaded = slicer.mrmlScene.GetNodeByID(self.volumeSelector.currentNodeId)
        #     self.updateState()

    def _onFinishCaseBundleLoad_(self, result, id, ids, additionalFilePaths):
        """
        Event triggered after a volume and the additional files have been loaded for a case.
        In this case, it is important to load a previously existing xml file
        @param result:
        @param id:
        @param ids:
        @param additionalFilePaths:
        @return:
        """
        if result == Util.OK and additionalFilePaths and os.path.exists(additionalFilePaths[0]):
            # Try to load a previously existing fiducials file downloaded with the ACIL case navigator
            # Check if we loaded any fiducials file
            fileName = os.path.basename(additionalFilePaths[0])
            for ix, mm in enumerate(self.sliceMeasurements):
                if fileName == "{}_{}{}".format(id, mm, self.customExtension):
                    # Create the sliced volume
                    self.currentReslicedVolume = self.logic.run_reslicing_CLI(slicer.util.getNode(id), mm)
                    self.logic.loadFiducialsXml(self.currentReslicedVolume, additionalFilePaths[0])
                    self._checkNewVolume_(self.currentReslicedVolume)
                    self.sliceSelectionRadioButtonGroup.buttons()[ix].setChecked(True)
                    return
            self.logic.loadFiducialsXml(slicer.util.getNode(id), additionalFilePaths[0])

    def __onResliceButtonClicked__(self):
        currentNode = self.volumeSelector.currentNode()
        if currentNode is None:
            slicer.util.warningDisplay("Please select a volume to reslice")
            return
        checkedId = self.sliceSelectionRadioButtonGroup.checkedId()
        if checkedId < 0:
            slicer.util.warningDisplay("Please select a reslicing size")
            return

        spacing = self.sliceMeasurements[checkedId]
        outputNode = self.logic.run_reslicing_CLI(currentNode, spacing)
        # Set active node
        self.volumeSelector.setCurrentNode(outputNode)
        self.currentReslicedVolume = outputNode
        SlicerUtil.setActiveVolumeIds(outputNode.GetID())
        self._checkNewVolume_(outputNode)



    def setActiveFiducialsListNode(self, volumeNode, typesList, createIfNotExists=True):
        """ Overrriden. Create a fiducials list node corresponding to this volume and this type list.
        In this case
        :param volumeNode: Scalar volume node
        :param typesList: list of types-subtypes. It can be a region-type-artifact or any other combination
        :param createIfNotExists: create the fiducials node if it doesn't exist yet for this subtype list
        :return: fiducials volume node
        """
        if volumeNode == self.currentReslicedVolume:
            CIP_ParenchymaSubtypeTrainingWidget.setActiveFiducialsListNode(self, volumeNode, typesList, createIfNotExists=createIfNotExists)

    def _checkNewVolume_(self, newVolumeNode):
        if newVolumeNode == self.currentReslicedVolume and newVolumeNode is not None:
            # Only when we have resliced
            self.currentVolumeLoaded = newVolumeNode
            CIP_ParenchymaSubtypeTrainingWidget._checkNewVolume_(self,newVolumeNode)
            SlicerUtil.setFiducialsCursorMode(True, True)
            fidNode = slicer.mrmlScene.GetNodeByID(slicer.modules.markups.logic().GetActiveListID())
            displayNode = fidNode.GetDisplayNode()
            displayNode.SetTextScale(4)
            # spacing = newVolumeNode.GetName().split("_")[-1]
            self.customFileName = "{}{}".format(newVolumeNode.GetName(), self.customExtension)

# CIP_ParenchymaSubtypeTrainingWithReslicingLogic
#
class CIP_ParenchymaSubtypeTrainingWithReslicingLogic(CIP_ParenchymaSubtypeTrainingLogic):
    def __init__(self):
        CIP_ParenchymaSubtypeTrainingLogic.__init__(self)
        self.currentOriginalNode = None

    def saveCurrentFiducials(self, localFilePath, caseNavigatorWidget=None, callbackFunction=None, saveInRemoteRepo=False):
        """ Save all the fiducials for the current volume.
        The name of the file will be VolumeName_parenchymaTraining.xml"
        :param filePath: destination file (local)
        :param caseNavigatorWidget: case navigator widget (optional)
        :param callbackFunction: function to invoke when the file has been uploaded to the server (optional)
        """
        volume = slicer.mrmlScene.GetNodeByID(self.currentVolumeId)
        #fileName = volume.GetName() + Util.file_conventions_extensions[self._xmlFileExtensionKey_]
        # If there is already a xml file in the results directory, make a copy.
        #localFilePath = os.path.join(directory, fileName)
        if os.path.isfile(localFilePath):
            # Make a copy of the file for history purposes
            copyfile(localFilePath, localFilePath + "." + time.strftime("%Y%m%d.%H%M%S"))

        # Iterate over all the fiducials list nodes
        pos = [0,0,0]
        geometryTopologyData = gtd.GeometryTopologyData()
        geometryTopologyData.coordinate_system = geometryTopologyData.LPS
        # Get the transformation matrix LPS-->IJK
        matrix = Util.get_lps_to_ijk_transformation_matrix(volume)
        geometryTopologyData.lps_to_ijk_transformation_matrix = Util.convert_vtk_matrix_to_list(matrix)
        # Save origin of the volume
        geometryTopologyData.origin = volume.GetOrigin()
        # Save the ORIGINAL spacing/dimensions of the node (instead of the resliced node)
        geometryTopologyData.spacing = self.currentOriginalNode.GetSpacing()
        geometryTopologyData.dimensions = self.currentOriginalNode.GetImageData().GetDimensions()

        # Get the hashtable and seed from previously loaded GeometryTopologyData object (if available)
        if self.currentGeometryTopologyData is None:
            hashTable = {}
        else:
            hashTable = self.currentGeometryTopologyData.get_hashtable()
            geometryTopologyData.id_seed = self.currentGeometryTopologyData.id_seed

        # Get a timestamp that will be used for all the points
        timestamp = gtd.GeometryTopologyData.get_timestamp()

        for fidListNode in slicer.util.getNodes("{0}_fiducials_*".format(volume.GetName())).itervalues():
            # Get all the markups
            for i in range(fidListNode.GetNumberOfMarkups()):
                fidListNode.GetNthFiducialPosition(i, pos)
                # Get the type from the description (region will always be 0)
                desc = fidListNode.GetNthMarkupDescription(i)
                # Switch coordinates from RAS to LPS
                lps_coords = Util.ras_to_lps(list(pos))
                pointMetadata = self.getPointMetadataFromFiducialDescription(desc)
                p = gtd.Point(pointMetadata[0], pointMetadata[1], pointMetadata[2], lps_coords, description=pointMetadata[3])
                key = p.get_hash()
                if hashTable.has_key(key):
                    # Add previously existing point
                    geometryTopologyData.add_point(hashTable[key], fill_auto_fields=False)
                else:
                    # Add a new point with a precalculated timestamp
                    geometryTopologyData.add_point(p, fill_auto_fields=True)
                    p.timestamp = timestamp

        # Get the xml content file
        xml = geometryTopologyData.to_xml()
        # Save the file
        with open(localFilePath, 'w') as f:
            f.write(xml)

        # Use the new object as the current GeometryTopologyData
        self.currentGeometryTopologyData = geometryTopologyData

        # Upload to MAD if we are using the ACIL case navigator
        if saveInRemoteRepo:
             caseNavigatorWidget.uploadFile(localFilePath, callbackFunction=callbackFunction)

        # Mark the current volume as saved
        self.savedVolumes[volume.GetName()] = True

    def run_reslicing_CLI(self, volumeNode, spacingMm, scene=None):
        """
        Execute the "ResampleScalarVolume" CLI to reslice a volume
        @param volumeNode: Scalar node
        @param spacingMm: Float
        @param scene: MRML scene (default: Slicer)
        @return: Resliced scalar volume
        """
        if scene is None:
            scene = slicer.mrmlScene
        self.currentOriginalNode = volumeNode
        # Create the output volume
        outputVolume = scene.CreateNodeByClass(volumeNode.GetClassName())
        outputVolume.CreateDefaultDisplayNodes()
        scene.AddNode(outputVolume)
        outputVolume.SetName("{}_{}".format(volumeNode.GetName(), spacingMm))
        parameters = {}
        parameters['InputVolume'] = volumeNode.GetID()
        parameters['OutputVolume'] = outputVolume.GetID()
        parameters['outputPixelSpacing'] = "0,0,{}".format(spacingMm)
        parameters['interpolationType'] = 'nearestNeighbor'
        slicer.cli.run(slicer.modules.resamplescalarvolume, None, parameters, wait_for_completion=True)
        return outputVolume