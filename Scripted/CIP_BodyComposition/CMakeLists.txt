#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_BodyComposition)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  CIP_BodyComposition_logic/__init__
  CIP_BodyComposition_logic/BodyCompositionParameters.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/CIP_BodyComposition_ColorMap.ctbl
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
  # Additional build-time testing
  add_subdirectory(Testing)
#endif()

