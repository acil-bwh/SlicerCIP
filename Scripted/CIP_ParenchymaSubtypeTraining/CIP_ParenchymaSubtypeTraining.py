import os, sys
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

from CIP.logic.SlicerUtil import SlicerUtil
from CIP_PointsLabelling import CIP_PointsLabelling, CIP_PointsLabellingWidget, CIP_PointsLabellingLogic
# Note: this is necessary in development because of the python path dependency
# try:
#     from CIP_PointsLabelling import CIP_PointsLabelling, CIP_PointsLabellingWidget, CIP_PointsLabellingLogic
# except:
#     import inspect
#     path = os.path.dirname(inspect.getfile(inspect.currentframe()))
#     path = os.path.normpath(os.path.join(path, '../CIP_PointsLabelling'))        # We assume that CIP_Common is a sibling folder of the one that contains this module
#     sys.path.append(path)
#     from CIP_PointsLabelling import CIP_PointsLabelling, CIP_PointsLabellingWidget, CIP_PointsLabellingLogic

from CIP_ParenchymaSubtypeTrainingLogic.SubtypingParameters import SubtypingParameters


#
# CIP_ParenchymaSubtypeTraining

class CIP_ParenchymaSubtypeTraining(CIP_PointsLabelling):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Parenchyma Subtype Training"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName, "CIP_PointsLabelling"]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory",
                                    "Brigham and Women's Hospital"]
        self.parent.helpText = """Training parenchyma subtypes done quickly by an expert<br>
        +A quick tutorial of the module can be found <a href='ttps://chestimagingplatform.org/files/chestimagingplatform/files/parenchymasubtypetraining_tutorial.pdf'>here</a>"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText


#
# CIP_ParenchymaSubtypeTrainingWidget
#
class CIP_ParenchymaSubtypeTrainingWidget(CIP_PointsLabellingWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        CIP_PointsLabellingWidget.__init__(self, parent)

    def _initLogic_(self):
        """Create a new logic object for the plugin"""
        self.logic = CIP_ParenchymaSubtypeTrainingLogic()

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        CIP_PointsLabellingWidget.setup(self)

        # Part of the GUI will be inherited. We just fill the radio buttons area
        # Radio buttons frame
        self.radioButtonsLayout = qt.QHBoxLayout(self.radioButtonsFrame)
        self.typesFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.typesFrame)
        self.typesLayout = qt.QVBoxLayout(self.typesFrame)

        labelsStyle = "font-weight: bold; margin: 0 0 10px 0px;"
        # Types Radio Buttons
        typesLabel = qt.QLabel("Select type")
        typesLabel.setStyleSheet(labelsStyle)
        self.typesLayout.addWidget(typesLabel)
        self.typesRadioButtonGroup = qt.QButtonGroup()
        for key in self.logic.params.mainTypes.keys():
            rbitem = qt.QRadioButton(self.logic.params.getMainTypeLabel(key))
            self.typesRadioButtonGroup.addButton(rbitem, key)
            self.typesLayout.addWidget(rbitem)
        self.typesRadioButtonGroup.buttons()[0].setChecked(True)

        # Subtypes Radio buttons
        # The content will be loaded dynamically every time the main type is modified
        self.subtypesFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.subtypesFrame)
        self.subtypesLayout = qt.QVBoxLayout(self.subtypesFrame)
        subtypesLabel = qt.QLabel("Select subtype")
        subtypesLabel.setStyleSheet(labelsStyle)
        self.subtypesLayout.addWidget(subtypesLabel)
        self.subtypesLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.subtypesRadioButtonGroup = qt.QButtonGroup()
        # Add all the subtypes (we will filter later in "updateState" function)
        for key in self.logic.params.subtypes.keys():
            # Build the description
            rbitem = qt.QRadioButton(self.logic.params.getSubtypeLabel(key))
            self.subtypesRadioButtonGroup.addButton(rbitem, key)
            self.subtypesLayout.addWidget(rbitem, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.subtypesLayout.addStretch()

        # Region radio buttons
        self.regionsFrame = qt.QFrame()
        self.radioButtonsLayout.addWidget(self.regionsFrame)
        self.regionsLayout = qt.QVBoxLayout(self.regionsFrame)
        regionsLabel = qt.QLabel("Select region")
        regionsLabel.setStyleSheet(labelsStyle)
        self.regionsLayout.addWidget(regionsLabel)
        self.regionsLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.regionsLayout.setStretch(0, 0)
        self.regionsRadioButtonGroup = qt.QButtonGroup()
        self.regionsFrame = qt.QFrame()
        # Add all the regions
        for key in self.logic.params.regions.keys():
            # Build the description
            rbitem = qt.QRadioButton(self.logic.params.getRegionLabel(key))
            self.regionsRadioButtonGroup.addButton(rbitem, key)
            self.regionsLayout.addWidget(rbitem, SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.regionsLayout.addStretch()
        self.regionsRadioButtonGroup.buttons()[0].setChecked(True)

        # Artifact radio buttons (Add them to the same layout as the type)
        self.separatorLabel = qt.QLabel("------------")
        labelsStyle = "margin: 5px 0 5px 0;"
        self.separatorLabel.setStyleSheet(labelsStyle)
        self.typesLayout.addWidget(self.separatorLabel)
        self.artifactsLabel = qt.QLabel("Select artifact")
        labelsStyle = "font-weight: bold; margin: 15px 0 10px 0;"
        self.artifactsLabel.setStyleSheet(labelsStyle)
        self.typesLayout.addWidget(self.artifactsLabel)
        self.artifactsRadioButtonGroup = qt.QButtonGroup()
        for artifactId in self.logic.params.artifacts.keys():
            rbitem = qt.QRadioButton(self.logic.params.getArtifactLabel(artifactId))
            self.artifactsRadioButtonGroup.addButton(rbitem, artifactId)
            self.typesLayout.addWidget(rbitem)
        self.artifactsRadioButtonGroup.buttons()[0].setChecked(True)

        self.typesLayout.setAlignment(SlicerUtil.ALIGNMENT_VERTICAL_TOP)
        self.typesLayout.addStretch()

        # Connections
        self.typesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onTypesRadioButtonClicked__)
        self.subtypesRadioButtonGroup.connect("buttonClicked (QAbstractButton*)",
                                              self.__onSecondaryRadioButtonClicked__)
        self.regionsRadioButtonGroup.connect("buttonClicked (QAbstractButton*)", self.__onSecondaryRadioButtonClicked__)
        self.artifactsRadioButtonGroup.connect("buttonClicked (QAbstractButton*)",
                                               self.__onSecondaryRadioButtonClicked__)

        self.updateState()

    def cleanup(self):
        pass

    def updateState(self):
        """ Refresh the markups state, activate the right fiducials list node (depending on the
        current selected type) and creates it when necessary
        :return:
        """
        # Load the subtypes for this type
        subtypesDict = self.logic.getSubtypes(self.typesRadioButtonGroup.checkedId())

        # Hide/Show the subtypes for this type
        for b in self.subtypesRadioButtonGroup.buttons():
            id = self.subtypesRadioButtonGroup.id(b)
            if id in subtypesDict:
                b.show()
            else:
                b.hide()
        # Check first element by default
        self.subtypesRadioButtonGroup.buttons()[0].setChecked(True)

        # Set the correct state for fiducials
        if self.currentVolumeLoaded is not None:
            typesList = (self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId()
                         , self.regionsRadioButtonGroup.checkedId(), self.artifactsRadioButtonGroup.checkedId())
            self.logic.setActiveFiducialsListNode(self.currentVolumeLoaded, typesList)

    # def _getColorTable_(self):
    #     """ Color table for this module for a better labelmap visualization.
    #     This must be implemented by child classes"""
    #     colorTableNode = SlicerUtil.getNode("CIP_ILDClassification_ColorMap*")
    #     if colorTableNode is None:
    #         # Load the node from disk
    #         p = os.path.join(os.path.dirname(os.path.realpath(__file__)),
    #                          "Resources/CIP_ILDClassification_ColorMap.ctbl")
    #         colorTableNode = slicer.modules.colors.logic().LoadColorFile(p)
    #     return colorTableNode

    # def __onNewILDClassificationLabelmapLoaded__(self, labelmapNode, split1, split2):
    #     """ Load a new ILD classification labelmap volume.
    #     If the labelmap is a known labelmap type, set the right colors and opacity
    #     @param labelmapNode:
    #     """
    #     if SlicerUtil.isExtensionMatch(labelmapNode, "ILDClassificationLabelmap"):
    #         colorNode = self._getColorTable_()
    #         displayNode = labelmapNode.GetDisplayNode()
    #         displayNode.SetAndObserveColorNodeID(colorNode.GetID())
    #         # Change Opacity
    #         SlicerUtil.displayLabelmapVolume(labelmapNode.GetID())
    #         SlicerUtil.changeLabelmapOpacity(0.3)

    def __onTypesRadioButtonClicked__(self, button):
        """ One of the radio buttons has been pressed
        :param button:
        :return:
        """
        self.updateState()

    def __onSecondaryRadioButtonClicked__(self, button):
        """ One of the subtype radio buttons has been pressed
        :param button:
        :return:
        """
        selectedVolume = self.volumeSelector.currentNode()
        if selectedVolume is not None:
            typesList = (self.typesRadioButtonGroup.checkedId(), self.subtypesRadioButtonGroup.checkedId(),
                         self.regionsRadioButtonGroup.checkedId(), self.artifactsRadioButtonGroup.checkedId())
            self.logic.setActiveFiducialsListNode(selectedVolume, typesList)


# CIP_ParenchymaSubtypeTrainingLogic
#
class CIP_ParenchymaSubtypeTrainingLogic(CIP_PointsLabellingLogic):
    def __init__(self):
        CIP_PointsLabellingLogic.__init__(self)
        self._params_ = SubtypingParameters()

    @property
    def _xmlFileExtensionKey_(self):
        """Overrriden. Key of the dictionary of file conventions that will be used in this module"""
        return "ParenchymaTrainingFiducialsXml"

    @property
    def params(self):
        """Overrriden. Params manager object"""
        if self._params_ is None:
            raise NotImplementedError("Object _params_ should be initialized in a child class")
        return self._params_

    def getSubtypes(self, typeId):
        """ Get all the subtypes for the specified type
        :param typeId: type id
        :return: Dictionary with Key=subtype_id and Value=tuple with subtypes features """
        return self.params.getSubtypes(typeId)

    def getTypeId(self, typesList):
        return typesList[0]

    def getSubtypeId(self, typesList):
        return typesList[1]

    def getRegionId(self, typesList):
        return typesList[2]

    def getArtifactId(self, typesList):
        return typesList[3]

    def getEffectiveType(self, typeId, subtypeId):
        """ Return the subtype id unless it's 0. In this case, return the main type id
        :param typeId:
        :param subtypeId:
        :return:
        """
        return typeId if subtypeId == 0 else subtypeId

    def _createFiducialsListNode_(self, nodeName, typesList):
        """ Overrriden. Create a fiducials node based on the types list specified.
        Depending on the child class, the number of types-subtypes will change, so every child class should
        have its own implementation
        :param nodeName: name of the fiducial node, created like Subtype_Region_Artifact  (Subtype could be a Main type)
        :param typesList: list of types
        :return: fiducials list node
        """
        fidListID = self.markupsLogic.AddNewFiducialNode(nodeName, slicer.mrmlScene)
        fidNode = slicer.mrmlScene.GetNodeByID(fidListID)
        displayNode = fidNode.GetDisplayNode()
        typeId = self.getTypeId(typesList)
        artifactId = self.getArtifactId(typesList)
        # The color will be based just in the main type and if it's an artifact
        displayNode.SetSelectedColor(self.params.getColor(typeId, artifactId))
        displayNode.SetTextScale(2)

        # Add an observer when a new markup is added
        fidNode.AddObserver(fidNode.PointPositionDefinedEvent, self.onMarkupAdded)

        return fidNode

    def setActiveFiducialsListNode(self, volumeNode, typesList, createIfNotExists=True):
        """ Overrriden. Create a fiducials list node corresponding to this volume and this type list.
        In this case
        :param volumeNode: Scalar volume node
        :param typesList: list of types-subtypes. It can be a region-type-artifact or any other combination
        :param createIfNotExists: create the fiducials node if it doesn't exist yet for this subtype list
        :return: fiducials volume node
        """
        typeId = self.getTypeId(typesList)
        artifactId = self.getArtifactId(typesList)
        regionId = self.getRegionId(typesList)
        if volumeNode is not None:
            if artifactId == -1:
                # No artifact
                nodeName = "{}_fiducials_{}_{}".format(volumeNode.GetName(), typeId, regionId)
            else:
                # Artifact. Add the type of artifact to the node name
                nodeName = "{}_fiducials_{}_{}_{}".format(volumeNode.GetName(), typeId, regionId, artifactId)
            fid = SlicerUtil.getNode(nodeName)
            if fid is None and createIfNotExists:
                SlicerUtil.logDevelop("DEBUG: creating a new fiducials node: " + nodeName)
                fid = self._createFiducialsListNode_(nodeName, typesList)
                # Add the volume to the list of "managed" cases
                self.savedVolumes[volumeNode.GetName()] = False

            self.currentVolumeId = volumeNode.GetID()
            self.currentTypesList = typesList
            # Mark the node list as the active one
            self.markupsLogic.SetActiveListID(fid)
            return fid

    def getPointMetadataFromFiducialDescription(self, description):
        """
        Overriden. Get the main metadata for a GeometryTopologyObject Point object (region, type, feature, description)
        from a fiducial description
        :param description: fiducial description
        :return: (region, type, feature, description) tuple for a point initialization
        """
        spl = description.split("_")
        typeId = int(spl[0])
        regionId = int(spl[1])
        artifactId = int(spl[2])
        # Point description will not be used
        return (regionId, typeId, artifactId, None)

    def getMarkupLabel(self, typesList):
        """
        Overriden. Get the text that will be displayed in the fiducial for the corresponding types-subtypes combination.
        The format is:
        TypeAbbreviation[-RegionAbbreviation][-Artifact]
        :param typesList: tuple (type-subtype-region-artifact)
        :return: label string for this fiducial
        """
        typeId = self.getTypeId(typesList)
        subtypeId = self.getSubtypeId(typesList)
        regionId = self.getRegionId(typesList)
        artifactId = self.getArtifactId(typesList)

        if subtypeId == 0:
            # No subtype. Just add the general type description
            typeLabel = self.params.getMainTypeAbbreviation(typeId)
        else:
            # Initials of the subtype
            typeLabel = self.params.getSubtypeAbbreviation(subtypeId)

        regionLabel = "-{}".format(self.params.getRegionAbbreviation(regionId)) if regionId != 0 else ""
        artifactLabel = "-{}".format(self.params.getArtifactAbbreviation(artifactId)) if artifactId != 0 else ""
        return typeLabel + regionLabel + artifactLabel

    def getTypesListFromXmlPoint(self, geometryTopologyDataPoint):
        """
        Overriden. Get a list of types that the module will use to operate from a Point object in a GeometryTopologyData object
        :param geometryTopologyDataPoint: GeometryTopologyData.Point object
        :return: tuple (typeId, subtypeId, artifactId)
        """
        subtype = geometryTopologyDataPoint.chest_type
        if subtype in list(self.params.mainTypes.keys()):
            # Main type. The subtype will be "Any"
            mainType = subtype
            subtype = 0
        else:
            mainType = self.params.getMainTypeForSubtype(subtype)

        return (mainType, subtype, geometryTopologyDataPoint.chest_region, geometryTopologyDataPoint.feature_type)

    def onMarkupAdded(self, markupListNode, event):
        """
        New markup node added. It will be renamed based on the type-subtype
        :param markupListNode: Markup LIST Node that was added
        :param event:
        :return:
        """
        label = self.getMarkupLabel(self.currentTypesList)
        # Get the last added markup (there is no index in the event!)
        n = markupListNode.GetNumberOfFiducials()
        # Change the label
        markupListNode.SetNthMarkupLabel(n - 1, label)
        # Use the description to store the type of the fiducial that will be saved in
        # the GeometryTopolyData object
        currentTypeId = self.getTypeId(self.currentTypesList)
        currentSubTypeId = self.getSubtypeId(self.currentTypesList)
        currentRegionId = self.getRegionId(self.currentTypesList)
        currentArtifactId = self.getArtifactId(self.currentTypesList)
        markupListNode.SetNthMarkupDescription(n - 1,
                                               "{}_{}_{}".format(
                                                   self.getEffectiveType(currentTypeId, currentSubTypeId),
                                                   currentRegionId,
                                                   currentArtifactId))
        # Markup added. Mark the current volume as state modified
        self.savedVolumes[self.currentVolumeId] = False


class CIP_ParenchymaSubtypeTrainingTest(ScriptedLoadableModuleTest):
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_CIP_ParenchymaSubtypeTraining()

    def test_CIP_ParenchymaSubtypeTraining(self):
        self.delayDisplay('Test not implemented!')
