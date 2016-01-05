#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_GetImage)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  CIP_GetImage_Resources/WinSCP.com
  CIP_GetImage_Resources/WinSCP.exe
  CIP_GetImage_Resources/WinSCP.ini
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  #WITH_GENERIC_TESTS
  #WITH_SUBDIR
  )

