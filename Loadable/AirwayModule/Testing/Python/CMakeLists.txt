#-----------------------------------------------------------------------------
#ctkMacroCompilePythonScript(
#  TARGET_NAME ScriptedLoadableExtensionTemplate
#  SCRIPTS "${MODULE_PYTHON_SCRIPTS}"
#  RESOURCES "${MODULE_PYTHON_RESOURCES}"
#  DESTINATION_DIR ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
#  INSTALL_DIR ${Slicer_INSTALL_QTSCRIPTEDMODULES_LIB_DIR}
#  NO_INSTALL_SUBDIR
#  )

#-----------------------------------------------------------------------------

# this will regiester the unittest subclass in the main script
# as a ctest (note that it is also usable as a runtime test).

if(Slicer_USE_QtTesting AND Slicer_USE_PYTHONQT)

  slicer_add_python_unittest(
    SCRIPT test_airwaymodule_loadsave.py
    SLICER_ARGS --no-main-window --disable-cli-modules --disable-loadable-modules --disable-scripted-loadable-modules
    TESTNAME_PREFIX nomainwindow_
    )

  SET(KIT_PYTHON_SCRIPTS
    ${KIT_PYTHON_SCRIPTS}
    test_airwaymodule_loadsave.py
  )

endif()

#add_test(
#  NAME test_airwaymodule_loadsave.py
#  COMMAND ${Slicer_LAUNCH_COMMAND} $<TARGET_FILE:SlicerApp${SlicerApp_EXE_SUFFIX}>
# --ignore-slicerrc --disable-cli-modules --disable-loadable-modules --disable-scripted-loadable-modules --no-main-window
#  --python-code "exit(slicer.util.EXIT_SUCCESS)"
#  )



