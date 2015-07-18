project(vtkSlicer${MODULE_NAME}ModuleLogic)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_LOGIC_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  )

set(${KIT}_SRCS
vtkSlicerAirwayInspectorModuleLogic.cxx
#vtkMaskBoundingBox.cxx
#vtkLungIntensityCorrection.cxx
#vtkSmoothLines.cxx
#vtkExtractAirwayTree.cxx
#vtkImageKernel.cxx
#vtkImageKernelSource.cxx
#vtkGeneralizedQuadratureKernelSource.cxx
#vtkComputeMonogenicSignal.cxx
#vtkGeneralizedPhaseCongruency.cxx
#vtkImageResliceWithPlane.cxx
#vtkComputeCentroid.cxx
#vtkImageReformatAlongRay.cxx
#vtkComputeAirwayWall.cxx
#vtkEllipseFitting.cxx
#vtkMultipleReconstructionKernelsPhaseCongruency.cxx
#vtkNRRDExport.cxx
#vtkImageTubularConfidence.cxx
#vtkTubularScaleSelection.cxx
#vtkTubularScalePolyDataFilter.cxx
#vtkComputeAirwayWallPolyData.cxx
#vtkImageReformatAlongRay2.cxx
  )

set(${KIT}_TARGET_LIBRARIES
  ${VTK_LIBRARIES}
  vtkSlicer${MODULE_NAME}ModuleMRML
  vtkSlicerVolumesModuleLogic
  ${CIP_LIBRARIES}
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleLogic(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )
