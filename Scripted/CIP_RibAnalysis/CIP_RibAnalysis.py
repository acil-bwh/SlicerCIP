import os
import re
import logging
import numpy as np
import slicer
from slicer.ScriptedLoadableModule import *


# TotalSegmentator rib structures (original label indices 92-115). SlicerTotalSegmentator sets each
# segment's ID to these structure names, so ribs can be matched by ID/name directly.
RIB_STRUCTURE_NAMES = [f"rib_left_{i}" for i in range(1, 13)] + \
                      [f"rib_right_{i}" for i in range(1, 13)]

# Anatomical rib regions, by level.
# True ribs (1-7) attach directly to the sternum via their own costal cartilage.
# False ribs (8-10) attach indirectly, via the cartilage of the rib above.
# Floating ribs (11-12) have no anterior attachment at all.
# Note: level 1 was excluded from the "true" rib region due to inconsitencies in segmentations due to FOV.
# Adjust RIB_REGIONS if you want level 1 included.
RIB_REGIONS = [
    ("True Rib Region", range(2, 8)),     # levels 2-7
    ("False Rib Region", range(8, 11)),   # levels 8-10
    ("Floating Rib Region", range(11, 13)),  # levels 11-12
]


#
# CIP_RibAnalysis
#

class CIP_RibAnalysis(ScriptedLoadableModule):
    """Analyzes rib segmentations to extract volume, mass, and density metrics based on parenchyma analysis equations"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "CIP Rib Analysis"
        self.parent.categories = ["Chest Imaging Platform"]
        self.parent.dependencies = []
        self.parent.contributors = ["Applied Chest Imaging Laboratory"]
        self.parent.helpText = """
Analyzes rib segmentations from TotalSegmentator to extract per level metrics (right and level sides were averaged to account
for segmentation errors:
- Volume 
- Mass 
- Density 
- Aggregated metrics for True/False/Floating rib regions and all ribs combined

WORKFLOW:
1. Load CT image and rib segmentation (e.g. from TotalSegmentator) in Slicer
2. Load this module
3. Select the CT volume and rib segmentation
4. Click "Analyze" to get metrics table
"""


#
# CIP_RibAnalysisWidget
#

class CIP_RibAnalysisWidget(ScriptedLoadableModuleWidget):
    """Widget for rib analysis"""

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        
        # Load UI
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CIP_RibAnalysis.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        
        # Set MRML scene on all widgets
        uiWidget.setMRMLScene(slicer.mrmlScene)
        self.ui.ctInputSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.ribSegmentationSelector.setMRMLScene(slicer.mrmlScene)
        self.ui.outputTableSelector.setMRMLScene(slicer.mrmlScene)
        
        # Create logic
        self.logic = CIP_RibAnalysisLogic()
        
        # Connect buttons
        self.ui.analyzeButton.clicked.connect(self.onAnalyzeButton)
        
        # Connect selectors for button state updates
        self.ui.ctInputSelector.currentNodeChanged.connect(self.updateButtonStates)
        self.ui.ribSegmentationSelector.currentNodeChanged.connect(self.updateButtonStates)
        
        # Initial button state
        self.updateButtonStates()

    def updateButtonStates(self):
        """Enable/disable buttons based on selections"""
        # Analysis needs both the CT image (for HU-based density) and the rib segmentation.
        self.ui.analyzeButton.enabled = (
            self.ui.ctInputSelector.currentNode() is not None
            and self.ui.ribSegmentationSelector.currentNode() is not None
        )

    def onAnalyzeButton(self):
        """Analyze rib segmentation"""
        try:
            ribSegmentation = self.ui.ribSegmentationSelector.currentNode()
            ctVolume = self.ui.ctInputSelector.currentNode()

            if not ribSegmentation:
                slicer.util.errorDisplay("Please select a rib segmentation")
                return

            if not ctVolume:
                slicer.util.errorDisplay("Please select a CT volume (required for HU-based density)")
                return
            
            # Create output table if needed
            outputTable = self.ui.outputTableSelector.currentNode()
            if not outputTable:
                outputTable = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
                outputTable.SetName("RibAnalysis_Results")
                self.ui.outputTableSelector.setCurrentNode(outputTable)
            
            # Run analysis
            self.ui.analyzeButton.enabled = False
            self.ui.analyzeButton.setText("Analyzing...")
            slicer.app.processEvents()
            
            self.logic.analyzeRibs(ribSegmentation, ctVolume, outputTable)
            
            # Display table in the view
            self.ui.resultsTableView.setMRMLScene(slicer.mrmlScene)
            self.ui.resultsTableView.setMRMLTableNode(outputTable)
            
            slicer.util.infoDisplay("Analysis complete!")
            
        except Exception as e:
            slicer.util.errorDisplay(f"Analysis failed: {str(e)}")
            logging.error(f"Analysis error: {e}", exc_info=True)
        finally:
            self.ui.analyzeButton.enabled = True
            self.ui.analyzeButton.setText("Analyze")


#
# CIP_RibAnalysisLogic
#

class CIP_RibAnalysisLogic(ScriptedLoadableModuleLogic):
    """Logic for rib analysis"""

    def analyzeRibs(self, ribSegmentationNode, ctVolumeNode, outputTableNode):
        """Compute per-rib volume, density and mass from a TotalSegmentator rib segmentation.

        Each rib segment is identified by its segment ID/name (rib_left_1 ... rib_right_12).
        From each segment, volume and mass are extracted and then aggregated via the mean for the levels.
        Then density is computed as mass/volume for each rib level.
        Finally, aggregate metrics for the True/False/Floating rib regions and all ribs combined are computed and added to the results table.
        """
        logging.info("Starting rib analysis...")

        if ctVolumeNode is None:
            raise ValueError("A CT volume is required for HU-based density.")

        ct_array = slicer.util.arrayFromVolume(ctVolumeNode)  # (k, j, i)
        spacing = ctVolumeNode.GetSpacing()
        cubicMMPerVoxel = spacing[0] * spacing[1] * spacing[2]
        voxelVolCm3 = cubicMMPerVoxel / 1000.0
        logging.info(f"Spacing: {spacing}, voxel volume: {voxelVolCm3} cm^3")

        # Identify and measure each rib segment.
        segmentation = ribSegmentationNode.GetSegmentation()
        ribMetrics = {}  # keyed by (side, level)
        for i in range(segmentation.GetNumberOfSegments()):
            segId = segmentation.GetNthSegmentID(i)
            segName = segmentation.GetSegment(segId).GetName()

            rib = self._segmentToRib(segId, segName)
            if rib is None:
                continue
            side, level = rib

            mask = slicer.util.arrayFromSegmentBinaryLabelmap(
                ribSegmentationNode, segId, ctVolumeNode
            )
            hu = ct_array[mask > 0]
            voxelCount = int(hu.size)
            if voxelCount == 0:
                continue

            volumeCm3 = voxelCount * voxelVolCm3
            massG = self.mass(hu, cubicMMPerVoxel)  # piecewise HU -> mass (g)
            meanDensity = massG / volumeCm3 if volumeCm3 > 0 else 0.0

            ribMetrics[(side, level)] = {
                'side': side,
                'level': level,
                'ts_label': self._ribLabelValue(side, level),
                'volume_cm3': volumeCm3,
                'mean_hu': float(hu.mean()),
                'sum_hu': float(hu.sum()),
                'voxel_count': voxelCount,
                'density': meanDensity,
                'mass_grams': massG,
            }

        if not ribMetrics:
            raise ValueError(
                "No rib segments found. Expected segments named rib_left_1 ... rib_right_12 "
                "(from TotalSegmentator)."
            )

        logging.info(f"Measured {len(ribMetrics)} rib segments")
        self._populateResultsTable(outputTableNode, ribMetrics)
        self._colorRibsByDensity3D(ribSegmentationNode, ribMetrics)
        self._showRegionDensityChart(ribMetrics)
        logging.info("Rib analysis complete")

    def _segmentToRib(self, segmentId, segmentName):
        """Return for a rib segment, or None if it isn't a rib.

        Works for raw TotalSegmentator IDs (rib_left_1) and terminology display names
        (e.g. "Left 1st rib") that the standard-names option may apply.
        """
        for text in (segmentId, segmentName):
            if not text:
                continue
            t = text.lower()
            if "rib" not in t:
                continue
            sideMatch = re.search(r"(left|right)", t)
            levelMatch = re.search(r"(\d{1,2})", t)
            if sideMatch and levelMatch:
                level = int(levelMatch.group(1))
                if 1 <= level <= 12:
                    return ("L" if sideMatch.group(1) == "left" else "R", level)
        return None

    def _ribLabelValue(self, side, level):
        # TotalSegmentator label values: rib left 1..12 -> 92..103, rib right 1..12 -> 104..115.
        return (91 if side == 'L' else 103) + level

    def mass(self, data, cubicMMPerVoxel):
        # This quantity is computed in a piecewise linear form
        # according to the prescription presented in ref. [1].
        # Mass is computed in grams. First compute the
        # contribution in HU interval from -98 and below.
        pheno_val = 0.0
        HU_tmp = data[data < -98].clip(-1000)
        if HU_tmp.shape[0] > 0:
            m = (1.21e-3 - 0.93) / (-1000 + 98)
            b = 1.21e-3 + 1000 * m
            pheno_val += np.sum((m * HU_tmp + b) * cubicMMPerVoxel * 0.001)

        # Now compute the mass contribution in the interval
        # [-98, 18] HU. Note the in the original paper, the
        # interval is defined from -98HU to 14HU, but we
        # extend in slightly here so there are no gaps in
        # coverage. The values we report in the interval
        # [14, 23] should be viewed as approximate.
        HU_tmp = data[np.logical_and(data >= -98, data <= 18)]
        if HU_tmp.shape[0] > 0:
            pheno_val += \
                np.sum((1.018 + 0.893 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        # Compute the mass contribution in the interval
        # (18, 100]
        HU_tmp = data[np.logical_and(data > 18, data <= 100)]
        if HU_tmp.shape[0] > 0:
            pheno_val += np.sum((1.003 + 1.169 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        # Compute the mass contribution in the interval > 100
        HU_tmp = data[data > 100]
        if HU_tmp.shape[0] > 0:
            pheno_val += np.sum((1.017 + 0.592 * HU_tmp / 1000.0) * cubicMMPerVoxel * 0.001)

        return pheno_val

    def _colorRibsByDensity3D(self, ribSegmentationNode, ribMetrics):
        """Show all rib segments in the 3D view. Highlight the ribs used for the main metrics.
        True Rib levels (2-7) are colored a single flat blue color; all other rib levels (1, and 8-12) 
        are colored a flat neutral gray. Both groups are visible together.

        Also shows a 3D corner annotation with the True Rib Region average density,
        which is the main metric used in the paper.
        """
        TRUE_RIB_COLOR = (0.2, 0.4, 0.85)    # flat blue for all True ribs
        GRAY = (0.7, 0.7, 0.7)              # flat gray for every other rib level

        trueLevels = set(range(2, 8))
        otherLevels = {1} | set(range(8, 13))  # level 1 (excluded), plus False (8-10) and Floating (11-12)

        trueRibs = {key: m for key, m in ribMetrics.items() if key[1] in trueLevels}
        otherRibs = {key: m for key, m in ribMetrics.items() if key[1] in otherLevels}

        if not trueRibs:
            logging.warning("No True Rib segments (levels 2-7) found; skipping 3D display.")
            return

        segmentation = ribSegmentationNode.GetSegmentation()
        displayNode = ribSegmentationNode.GetDisplayNode()
        if displayNode is None:
            ribSegmentationNode.CreateDefaultDisplayNodes()
            displayNode = ribSegmentationNode.GetDisplayNode()

        # Build a lookup from (level) back to the actual segment ID, since
        # ribMetrics is keyed by (level) but display colors are set per segment ID.
        keyToSegmentId = {}
        allSegmentIds = []
        for i in range(segmentation.GetNumberOfSegments()):
            segId = segmentation.GetNthSegmentID(i)
            allSegmentIds.append(segId)
            segName = segmentation.GetSegment(segId).GetName()
            rib = self._segmentToRib(segId, segName)
            if rib is not None:
                keyToSegmentId[rib] = segId

        ribSegmentIds = set(keyToSegmentId.values())

        # This segmentation may contain non-rib structures (e.g. lungs, vertebrae,
        # sternum) if it came from a broader TotalSegmentator run. Hide everything
        # that isn't one of the 24 rib segments so only ribs appear in the 3D view.
        for segId in allSegmentIds:
            if segId not in ribSegmentIds:
                displayNode.SetSegmentVisibility3D(segId, False)

        # True ribs (2-7): flat color, shown in 3D.
        for key in trueRibs:
            segId = keyToSegmentId.get(key)
            if segId is None:
                continue
            displayNode.SetSegmentOverrideColor(segId, *TRUE_RIB_COLOR)
            displayNode.SetSegmentVisibility3D(segId, True)

        # All other ribs (1, 8-12): flat gray, also shown in 3D.
        for key in otherRibs:
            segId = keyToSegmentId.get(key)
            if segId is None:
                continue
            displayNode.SetSegmentOverrideColor(segId, *GRAY)
            displayNode.SetSegmentVisibility3D(segId, True)

        # The segmentation only has 3D geometry once a "Closed surface" representation
        # has been generated -- SetVisibility3D alone does nothing if this doesn't
        # exist yet (e.g. fresh TotalSegmentator output, which is binary-labelmap-only).
        if not segmentation.ContainsRepresentation("Closed surface"):
            logging.info("Generating closed surface representation for 3D display...")
            segmentation.CreateRepresentation("Closed surface")

        # Make sure the segmentation is actually shown in 3D and a 3D view is visible.
        displayNode.SetVisibility3D(True)
        slicer.util.resetThreeDViews()
        layoutManager = slicer.app.layoutManager()
        if layoutManager is not None:
            layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

        # Show the True Rib Region average density as a 3D corner annotation.
        trueDensities = [m['density'] for m in trueRibs.values()]
        avgDensity = sum(trueDensities) / len(trueDensities)
        self._showRegionAnnotation3D(
            f"True Rib Region Density: {avgDensity:.4f} g/cm³ (shown in blue)"
        )

    def _showRegionAnnotation3D(self, text):
        """Display a text annotation in the 3D view's corner.

        Uses the 3D view's CornerAnnotation actor directly via the view's renderer,
        so no extra MRML nodes are needed.
        """
        layoutManager = slicer.app.layoutManager()
        if layoutManager is None or layoutManager.threeDViewCount == 0:
            return
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.cornerAnnotation().SetText(2, text)  # upper-right corner
        threeDView.cornerAnnotation().GetTextProperty().SetColor(1, 1, 1)
        threeDView.forceRender()

    def _aggregate(self, ribMetricsSubset):
        """Combine a list of per-rib level summation metric dicts into one aggregate row.
        """
        totalVolume = sum(m['volume_cm3'] for m in ribMetricsSubset)
        totalMass = sum(m['mass_grams'] for m in ribMetricsSubset)
        totalVoxels = sum(m['voxel_count'] for m in ribMetricsSubset)
        totalSumHu = sum(m['sum_hu'] for m in ribMetricsSubset)

        return {
            'volume_cm3': totalVolume,
            'mass_grams': totalMass,
            'density': (totalMass / totalVolume) if totalVolume > 0 else 0.0,
            'mean_hu': (totalSumHu / totalVoxels) if totalVoxels > 0 else 0.0,
        }

    def _aggregateSimpleAverage(self, ribMetricsSubset):
        """Combine a list of per-rib level average metric dicts into one region-summary row.
        """
        ribCount = len(ribMetricsSubset)
        if ribCount == 0:
            return {'volume_cm3': 0.0, 'mass_grams': 0.0, 'density': 0.0, 'mean_hu': 0.0}

        avgVolume = sum(m['volume_cm3'] for m in ribMetricsSubset) / ribCount
        avgMass = sum(m['mass_grams'] for m in ribMetricsSubset) / ribCount
        avgDensity = sum(m['density'] for m in ribMetricsSubset) / ribCount
        avgMeanHu = sum(m['mean_hu'] for m in ribMetricsSubset) / ribCount

        return {
            'volume_cm3': avgVolume,
            'mass_grams': avgMass,
            'density': avgDensity,
            'mean_hu': avgMeanHu,
        }

    # Custom layout ID for "2 stacked Plot views (replacing axial) + Coronal + Sagittal + 3D".
    REGION_DENSITY_LAYOUT_ID = 50601

    def _ensureRegionDensityLayout(self):
        """Register (once) a custom four-up layout where the axial (Red) slice
        slot is replaced by TWO stacked Plot views (density on top, mass below),
        keeping Coronal (Green), Sagittal (Yellow), and the 3D view as in the
        standard four-up layout. Does not alter or remove any other existing layouts.
        """
        layoutManager = slicer.app.layoutManager()
        if layoutManager is None:
            return None
        layoutLogic = layoutManager.layoutLogic()
        layoutNode = layoutLogic.GetLayoutNode()

        # If this custom layout description was already registered (e.g. a previous
        # analysis run in this session), don't re-register it.
        existingDescription = layoutNode.GetLayoutDescription(self.REGION_DENSITY_LAYOUT_ID)
        if existingDescription:
            return self.REGION_DENSITY_LAYOUT_ID

        customLayout = (
            "<layout type=\"vertical\" split=\"true\">"
            " <item><layout type=\"horizontal\">"
            "  <item><layout type=\"vertical\">"
            "   <item><view class=\"vtkMRMLPlotViewNode\" singletontag=\"PlotView1\">"
            "    <property name=\"viewlabel\" action=\"default\">P1</property>"
            "   </view></item>"
            "   <item><view class=\"vtkMRMLPlotViewNode\" singletontag=\"PlotView2\">"
            "    <property name=\"viewlabel\" action=\"default\">P2</property>"
            "   </view></item>"
            "  </layout></item>"
            "  <item><view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
            "   <property name=\"viewlabel\" action=\"default\">1</property>"
            "  </view></item>"
            " </layout></item>"
            " <item><layout type=\"horizontal\">"
            "  <item><view class=\"vtkMRMLSliceNode\" singletontag=\"Green\">"
            "   <property name=\"orientation\" action=\"default\">Coronal</property>"
            "   <property name=\"viewlabel\" action=\"default\">G</property>"
            "   <property name=\"viewcolor\" action=\"default\">#6EB04B</property>"
            "  </view></item>"
            "  <item><view class=\"vtkMRMLSliceNode\" singletontag=\"Yellow\">"
            "   <property name=\"orientation\" action=\"default\">Sagittal</property>"
            "   <property name=\"viewlabel\" action=\"default\">Y</property>"
            "   <property name=\"viewcolor\" action=\"default\">#EDD54C</property>"
            "  </view></item>"
            " </layout></item>"
            "</layout>"
        )
        layoutNode.AddLayoutDescription(self.REGION_DENSITY_LAYOUT_ID, customLayout)
        return self.REGION_DENSITY_LAYOUT_ID

    def _buildRegionBarChart(self, regionNames, regionValues, valueColumnName,
                              chartTitle, tableNodeAttrName, seriesNodeAttrName,
                              chartNodeAttrName):
        """Shared helper to build/update a (vertical) bar chart for the 3 rib
        regions, identifying each region via the LEGEND rather than axis tick text.

        Per the actual Slicer source (Libs/MRML/Core/vtkMRMLPlotChartNode.h and
        vtkMRMLPlotSeriesNode.h, fetched directly from GitHub):

        Returns the vtkMRMLPlotChartNode that was built/updated.
        """
        REGION_COLORS = {
            "True Rib Region": (0.2, 0.4, 0.85),     # blue, matches 3D True rib color
            "False Rib Region": (0.6, 0.6, 0.6),
            "Floating Rib Region": (0.3, 0.3, 0.3),
        }
        DEFAULT_COLOR = (0.5, 0.5, 0.5)
        numRegions = len(regionNames)

        # One table + one series PER region, so each series's Name shows up as its
        # own legend entry. Each table has a row for EVERY region's X position
        # (0..numRegions-1), with only this region's own row holding the real
        # value -- the rest are 0 -- so every series shares the same X spacing and
        # therefore the same computed bar width.
        seriesNodes = []
        for i, (name, value) in enumerate(zip(regionNames, regionValues)):
            tableAttr = f"{tableNodeAttrName}_{i}"
            seriesAttr = f"{seriesNodeAttrName}_{i}"

            chartTableNode = getattr(self, tableAttr, None)
            if chartTableNode is None or slicer.mrmlScene.GetNodeByID(chartTableNode.GetID()) is None:
                chartTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
                chartTableNode.SetName(f"RibAnalysis_{tableNodeAttrName}_{i}")
                setattr(self, tableAttr, chartTableNode)

            table = chartTableNode.GetTable()
            table.RemoveAllColumns()
            table.RemoveAllRows()

            indexCol = vtk.vtkFloatArray()
            indexCol.SetName("Region Index")
            valueCol = vtk.vtkFloatArray()
            valueCol.SetName(valueColumnName)
            for j in range(numRegions):
                indexCol.InsertNextValue(float(j))
                valueCol.InsertNextValue(value if j == i else 0.0)
            table.AddColumn(indexCol)
            table.AddColumn(valueCol)
            chartTableNode.Modified()

            plotSeriesNode = getattr(self, seriesAttr, None)
            if plotSeriesNode is None or slicer.mrmlScene.GetNodeByID(plotSeriesNode.GetID()) is None:
                plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode")
                setattr(self, seriesAttr, plotSeriesNode)
            plotSeriesNode.SetName(name)  # this populates the legend entry
            plotSeriesNode.SetAndObserveTableNodeID(chartTableNode.GetID())
            plotSeriesNode.SetXColumnName("Region Index")
            plotSeriesNode.SetYColumnName(valueColumnName)
            plotSeriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeBar)
            color = REGION_COLORS.get(name, DEFAULT_COLOR)
            plotSeriesNode.SetColor(*color)

            seriesNodes.append(plotSeriesNode)

        plotChartNode = getattr(self, chartNodeAttrName, None)
        if plotChartNode is None or slicer.mrmlScene.GetNodeByID(plotChartNode.GetID()) is None:
            plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
            plotChartNode.SetName(f"RibAnalysis_{chartNodeAttrName}")
            setattr(self, chartNodeAttrName, plotChartNode)

        plotChartNode.RemoveAllPlotSeriesNodeIDs()
        for seriesNode in seriesNodes:
            plotChartNode.AddAndObservePlotSeriesNodeID(seriesNode.GetID())
        plotChartNode.SetTitle(chartTitle)
        plotChartNode.SetXAxisTitle("Region")
        plotChartNode.SetYAxisTitle(valueColumnName)
        plotChartNode.SetLegendVisibility(True)   # region names identified here

        return plotChartNode

    def _showRegionDensityChart(self, ribMetrics):
        """Show two stacked bar charts for the True/False/Floating rib regions:
        Density (g/cm^3) on top, Mass (g) below. Both use the exact same per-region
        average computed for the results table (_aggregateSimpleAverage), so the
        charts always match it exactly. Replaces the axial (Red) slice view in the
        four-up layout; Coronal, Sagittal, and 3D are unchanged.
        """
        regionNames = []
        regionDensities = []
        regionMasses = []
        for regionName, levelRange in RIB_REGIONS:
            levels = set(levelRange)
            subset = [m for (side, level), m in ribMetrics.items() if level in levels]
            if not subset:
                continue
            aggregated = self._aggregateSimpleAverage(subset)
            regionNames.append(regionName)
            regionDensities.append(aggregated['density'])
            regionMasses.append(aggregated['mass_grams'])

        if not regionDensities:
            logging.warning("No rib region data available; skipping region charts.")
            return

        densityChartNode = self._buildRegionBarChart(
            regionNames, regionDensities,
            valueColumnName="Density (g/cm³)",
            chartTitle="Rib Region Density",
            tableNodeAttrName="_regionDensityChartTable",
            seriesNodeAttrName="_regionDensityPlotSeries",
            chartNodeAttrName="_regionDensityPlotChart",
        )
        massChartNode = self._buildRegionBarChart(
            regionNames, regionMasses,
            valueColumnName="Mass (g)",
            chartTitle="Rib Region Mass",
            tableNodeAttrName="_regionMassChartTable",
            seriesNodeAttrName="_regionMassPlotSeries",
            chartNodeAttrName="_regionMassPlotChart",
        )

        # Switch the axial (Red) slot in the four-up layout to two stacked Plot
        # views and show density (top) / mass (bottom) there. Coronal/Sagittal/3D
        # are unchanged.
        layoutManager = slicer.app.layoutManager()
        if layoutManager is None:
            return
        layoutId = self._ensureRegionDensityLayout()
        if layoutId is None:
            return
        layoutManager.setLayout(layoutId)

        if layoutManager.plotViewCount >= 1:
            plotWidget = layoutManager.plotWidget(0)
            if plotWidget is not None:
                plotWidget.mrmlPlotViewNode().SetPlotChartNodeID(densityChartNode.GetID())
        if layoutManager.plotViewCount >= 2:
            plotWidget = layoutManager.plotWidget(1)
            if plotWidget is not None:
                plotWidget.mrmlPlotViewNode().SetPlotChartNodeID(massChartNode.GetID())

    def _populateResultsTable(self, tableNode, ribMetrics):
        """Populate the output table with one row per rib LEVEL (1-12), averaging
        Left and Right together, plus aggregate rows for the True/False/Floating
        rib regions and an ALL RIBS totals row.
        """
        table = tableNode.GetTable()
        table.RemoveAllColumns()
        table.RemoveAllRows()

        labelCol = vtk.vtkStringArray()  # string so aggregate rows can leave it blank
        labelCol.SetName("TS Label")
        ribCol = vtk.vtkStringArray()
        ribCol.SetName("Rib")
        volCol = vtk.vtkFloatArray()
        volCol.SetName("Volume (cm³)")
        huCol = vtk.vtkFloatArray()
        huCol.SetName("Mean HU")
        densCol = vtk.vtkFloatArray()
        densCol.SetName("Density (g/cm³)")
        massCol = vtk.vtkFloatArray()
        massCol.SetName("Mass (g)")

        def addRow(label, rib, metrics):
            labelCol.InsertNextValue(label)    
            ribCol.InsertNextValue(rib)
            volCol.InsertNextValue(metrics['volume_cm3'])
            huCol.InsertNextValue(metrics['mean_hu'])
            densCol.InsertNextValue(metrics['density'])
            massCol.InsertNextValue(metrics['mass_grams'])

        # Per-level rows: levels 1..12, averaging Left and Right together (simple,
        # unweighted mean of the two sides -- same approach as _aggregateSimpleAverage).
        # If only one side is present for a level, that side's value is used as-is
        # (an "average" of one value is just that value).
        for level in range(1, 13):
            sidesPresent = [
                ribMetrics[key] for key in (('L', level), ('R', level)) if key in ribMetrics
            ]
            if not sidesPresent:
                continue
            levelMetrics = self._aggregateSimpleAverage(sidesPresent)

            # TS Label has no single value once both sides are merged; show both,
            # e.g. "95 / 107", so the row is still traceable to the TotalSegmentator IDs.
            tsLabels = "/".join(str(m['ts_label']) for m in sidesPresent)
            addRow(tsLabels, f"Rib Level {level}", levelMetrics)

        # Regional aggregate rows (True/False/Floating). Each row averages across
        # every rib in that region -- all levels in the range, both left and right
        # pooled together -- for Volume, Mass, Density, and Mean HU alike (simple,
        # unweighted mean; see _aggregateSimpleAverage). These are per-rib averages,
        # not regional totals.
        for regionName, levelRange in RIB_REGIONS:
            levels = set(levelRange)
            subset = [m for (side, level), m in ribMetrics.items() if level in levels]
            if not subset:
                continue
            addRow("", f"{regionName} (avg)", self._aggregateSimpleAverage(subset))

        # Grand totals row across all ribs.
        addRow("", "ALL RIBS", self._aggregate(list(ribMetrics.values())))

        table.AddColumn(labelCol)
        table.AddColumn(ribCol)
        table.AddColumn(huCol)
        table.AddColumn(massCol)
        table.AddColumn(volCol)
        table.AddColumn(densCol)

        tableNode.Modified()
        logging.info("Results table populated")


# Import VTK at end to avoid issues
import vtk