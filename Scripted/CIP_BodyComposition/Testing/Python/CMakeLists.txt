slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py
      SLICER_ARGS --additional-module-paths
      ${MODULE_BUILD_DIR}
      ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
 )
