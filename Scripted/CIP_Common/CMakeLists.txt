#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_Common)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  CIP/__init__.py
  CIP/logic/__init__.py
  CIP/logic/Colors.py
  CIP/logic/EventsTrigger.py
  CIP/logic/file_conventions.py
  CIP/logic/geometry_topology_data.py
  CIP/logic/SlicerUtil.py
  CIP/logic/SubtypingParameters.py
  CIP/logic/Util.py
  CIP/ui/__init__.py
  CIP/ui/AutoUpdateWidget.py
  CIP/ui/CaseReportsWidget.py
  CIP/ui/CIP_EditBox.py
  CIP/ui/CIP_EditorWidget.py
  CIP/ui/LoadSaveDataWidget.py
  CIP/ui/MIPViewerWidget.py
  )

set(MODULE_PYTHON_RESOURCES
  CIP/ui/Resources/Icons/1415667870_kview.png
  CIP/ui/Resources/Icons/ACIL.png
  CIP/ui/Resources/Icons/ACIL_Blank.png
  CIP/ui/Resources/Icons/Load.png
  CIP/ui/Resources/Icons/Reload.png
  CIP/ui/Resources/Icons/Save.png
  CIP/ui/Resources/Icons/SaveAll.png
  CIP/ui/Resources/Icons/WelcomeFiducialWithArrow-Original.png
  CIP/ui/Resources/Icons/analyze.png
  CIP/ui/Resources/Icons/axial.png
  CIP/ui/Resources/Icons/coronal.png
  CIP/ui/Resources/Icons/delete.png
  CIP/ui/Resources/Icons/export-csv.png
  CIP/ui/Resources/Icons/move_down.png
  CIP/ui/Resources/Icons/move_up.png
  CIP/ui/Resources/Icons/next.png
  CIP/ui/Resources/Icons/open_file.png
  CIP/ui/Resources/Icons/plus.png
  CIP/ui/Resources/Icons/previous.png
  CIP/ui/Resources/Icons/recycle.png
  CIP/ui/Resources/Icons/ruler.png
  CIP/ui/Resources/Icons/rulers.png
  CIP/ui/Resources/Icons/sagittal.png
  CIP/ui/Resources/StructuresColorMap.ctbl
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  #WITH_GENERIC_TESTS
  #WITH_SUBDIR
  )

#-----------------------------------------------------------------------------
#if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
 # slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  #add_subdirectory(Testing)
#endif()

