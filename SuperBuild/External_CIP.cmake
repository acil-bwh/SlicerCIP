
set(proj CIP)

# Set dependency list
set(${proj}_DEPENDENCIES)

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj DEPENDS_VAR ${proj}_DEPENDENCIES)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED CIP_DIR AND NOT EXISTS ${CIP_DIR})
  message(FATAL_ERROR "CIP_DIR variable is defined but corresponds to nonexistent directory")
endif()


#This check is because  default runtime associated with <=10.8 deployment target is 'libstdc++'
# if (APPLE)
#   if (${CMAKE_OSX_DEPLOYMENT_TARGET} VERSION_LESS "10.8")
#     set(CIP_CMAKE_CXX_FLAGS "-stdlib=libstdc++ -mmacosx-version-min=10.6")
#   endif()
# endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(NOT DEFINED git_protocol)
    set(git_protocol "git")
  endif()
  message(STATUS ${VTK_DIR})

  ExternalProject_Add(${proj}
    ${${proj}_EP_ARGS}
    GIT_REPOSITORY "${git_protocol}://github.com/acil-bwh/ChestImagingPlatform.git"
    GIT_TAG origin/develop
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    #DOWNLOAD_COMMAND ${CMAKE_COMMAND} -E echo "Remove this line and uncomment GIT_REPOSITORY and GIT_TAG"
    #SOURCE_DIR /Users/jonieva/Projects/CIP
    BINARY_DIR ${proj}-build
    CMAKE_CACHE_ARGS
      -DCIP_SUPERBUILD:BOOL=OFF
      -DCIP_INTEGRATE_WITH_SLICER:BOOL=ON
      -DITK_DIR:PATH=${ITK_DIR}
      -DVTK_DIR:PATH=${VTK_DIR}
      -DVTK_SOURCE_DIR:PATH=${VTK_SOURCE_DIR}
      -DTeem_DIR:PATH=${Teem_DIR}
      -DLIBXML2_INCLUDE_DIR:PATH=${vtklibxml2_INCLUDE_DIRS}
      -DLIBXML2_LIBRARIES:PATH=${vtklibxml2_LIBRARIES}
      -DJsonCpp_INCLUDE_DIR:PATH=${vtkjsoncpp_INCLUDE_DIRS}
      -DJsonCpp_LIBRARY:PATH=${vtkjsoncpp_LIBRARIES}
      -DBUILD_GENERATEMODEL:BOOL=OFF
      -DBUILD_GENERATESIMPLELUNGMASK:BOOL=OFF # temporarily off due to lack of VtkGlue
      -DBUILD_ComputeAirwayWallFromParticles:BOOL=OFF # temporarily off due to lack of VtkGlue
      -DPYTHON_EXECUTABLE:FILEPATH=${PYTHON_EXECUTABLE}    # To parse the convention files
      -DUSE_CYTHON:BOOL=OFF
      -DCIP_BUILD_TESTING_PYTHON:BOOL=OFF
      -DSlicerExecutionModel_DIR:STRING=${SlicerExecutionModel_DIR}
      -DSlicer_BUILD_CLI:BOOL=ON
      -DSlicer_BUILD_CLI_SUPPORT:BOOL=ON
      -DSlicerExecutionModel_DEFAULT_CLI_EXECUTABLE_LINK_FLAGS:STRING=-Wl,-rpath,@loader_path/../../../../../
      -DCIP_CLI_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${EXTENSION_BUILD_SUBDIRECTORY}/${Slicer_CLIMODULES_LIB_DIR}
      -DCIP_CLI_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${EXTENSION_BUILD_SUBDIRECTORY}/${Slicer_CLIMODULES_LIB_DIR}
      -DCIP_CLI_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${EXTENSION_BUILD_SUBDIRECTORY}/${Slicer_CLIMODULES_BIN_DIR}
      -DCIP_CLI_INSTALL_LIBRARY_DESTINATION:PATH=${Slicer_INSTALL_CLIMODULES_LIB_DIR}
      -DCIP_CLI_INSTALL_ARCHIVE_DESTINATION:PATH=${Slicer_INSTALL_CLIMODULES_LIB_DIR}
      -DCIP_CLI_INSTALL_RUNTIME_DESTINATION:PATH=${Slicer_INSTALL_CLIMODULES_BIN_DIR}
      -DCIP_PYTHON_INSTALL:BOOL=OFF
      -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      -DBUILD_TESTING:BOOL=OFF
      -DCMAKE_CXX_FLAGS:STRING=${CIP_CMAKE_CXX_FLAGS}
      -DCMAKE_CXX_STANDARD:STRING=${CMAKE_CXX_STANDARD}
      -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=${CMAKE_CXX_STANDARD_REQUIRED}
      -DCMAKE_CXX_EXTENSIONS:BOOL=${CMAKE_CXX_EXTENSIONS}
    INSTALL_COMMAND ""
    DEPENDS
      ${${proj}_DEPENDENCIES}
    )
  set(${proj}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)

else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()

mark_as_superbuild(${proj}_DIR:PATH)
