#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_Common)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  CIP/__init__.py
  CIP/logic/__init__.py
  CIP/logic/BodyCompositionParameters.py
  CIP/logic/GeometryTopologyData.py
  CIP/logic/SlicerUtil.py
  CIP/logic/StructuresParameters.py
  CIP/logic/Util.py
  CIP/ui/__init__.py
  CIP/ui/AutoUpdateWidget.py
  CIP/ui/CIP_EditBox.py
  CIP/ui/CIP_EditorWidget.py
  CIP/ui/LoadSaveDataWidget.py
  CIP/ui/CaseReportsWidget.py
  )

set(MODULE_PYTHON_RESOURCES
  CIP/ui/Resources/BodyCompositionColorMap.ctbl
  CIP/ui/Resources/StructuresColorMap.ctbl
  CIP/ui/Resources/Icons/previous.png
  CIP/ui/Resources/Icons/next.png
  CIP/ui/Resources/Icons/1415667870_kview.png
  CIP/ui/Resources/Icons/ACIL_Blank.png
  CIP/ui/Resources/Icons/export-csv.png
  CIP/ui/Resources/Icons/Load.png
  CIP/ui/Resources/Icons/Save.png
  CIP/ui/Resources/Icons/SaveAll.png
  CIP/ui/Resources/Icons/Reload.png
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

