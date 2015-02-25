cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
project(SlicerCIP)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://www.example.com/Slicer/Extensions/SlicerCIP-test")
set(EXTENSION_CATEGORY "Chest Imaging Platform")
set(EXTENSION_CONTRIBUTORS "Raul San Jose (ACIL), James Ross")
set(EXTENSION_DESCRIPTION "This is an example of an extension using SuperBuild to build a dependent project named Foo")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SlicerCIP-test.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SlicerCIP-test/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)


#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

find_package(LibXml2 REQUIRED)
mark_as_superbuild(LibXml2_DIR)


#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()


#-----------------------------------------------------------------------------
# Extension modules
#add_subdirectory(Example-Scripted)
#add_subdirectory(Example-Loadable)
#add_subdirectory(Example-CLI)
## NEXT_MODULE

#-----------------------------------------------------------------------------
add_subdirectory(Scripted)
add_subdirectory(Loadable)

if(BUILD_TESTING)
#  add_subdirectory(Testing)
endif()


#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
#Package CIP into SlicerCIP build….
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CIP_DIR};CIP;RuntimeLibraries;/")
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CIP_DIR};CIP;Runtime;/")

include(${Slicer_EXTENSION_CPACK})

