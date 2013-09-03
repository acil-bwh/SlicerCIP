project(vtkSlicer${MODULE_NAME}ModuleMRML)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_MRML_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  )


set(${KIT}_SRCS
  vtkMRMLAirwayDisplayNode.cxx
  vtkMRMLAirwayDisplayNode.h
  )
list(APPEND ${KIT}_SRCS
  #vtkMRMLAirwayGlyphDisplayNode.cxx
  #vtkMRMLAirwayGlyphDisplayNode.h
  #vtkMRMLAirwayLineDisplayNode.cxx
  #vtkMRMLAirwayLineDisplayNode.h
  #vtkMRMLAirwayTubeDisplayNode.cxx
  #vtkMRMLAirwayTubeDisplayNode.h
  vtkMRMLAirwayNode.cxx
  vtkMRMLAirwayNode.h
  vtkMRMLAirwayStorageNode.cxx
  vtkMRMLAirwayStorageNode.h
  )

set(${KIT}_TARGET_LIBRARIES
  ${ITK_LIBRARIES}
  ${MRML_LIBRARIES}
   vtkSlicerAnnotationsModuleMRML
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleMRML(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )
