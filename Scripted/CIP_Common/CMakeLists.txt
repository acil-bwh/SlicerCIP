#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_Common)
# Get all the cip_python files
get_filename_component(SOURCE_PYTHON_PATH ${CMAKE_BINARY_DIR}/../CIP-build/cip_python ABSOLUTE)
set (DESTINATION_PYTHON_PATH "${CMAKE_CURRENT_SOURCE_DIR}/CIP/logic")
file(COPY ${SOURCE_PYTHON_PATH} DESTINATION ${DESTINATION_PYTHON_PATH})

# Add all the python files under the current source directory (original+cip_python)
file(GLOB_RECURSE PYTHON_FILES "${CMAKE_CURRENT_SOURCE_DIR}/*.py" )
# Change to relative paths to adapt it to the slicerMacroBuildScriptedModule format
foreach(f ${PYTHON_FILES})
 file(RELATIVE_PATH RELATIVE_FILE_PATH ${CMAKE_CURRENT_SOURCE_DIR} ${f})
 list(APPEND MODULE_PYTHON_SCRIPTS ${RELATIVE_FILE_PATH})
endforeach()
# Do the same thing for the Resources
file (GLOB_RECURSE MODULE_PYTHON_RESOURCES_FULL_PATH "${CMAKE_CURRENT_SOURCE_DIR}/CIP/ui/Resources/*")
foreach(f ${MODULE_PYTHON_RESOURCES_FULL_PATH})
  file(RELATIVE_PATH RELATIVE_FILE_PATH ${CMAKE_CURRENT_SOURCE_DIR} ${f})
  list(APPEND MODULE_PYTHON_RESOURCES ${RELATIVE_FILE_PATH})
endforeach()

#message("****************")

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
