cmake_minimum_required(VERSION 3.5.0)

#-----------------------------------------------------------------------------
# Set C++ standard version and extensions
#-----------------------------------------------------------------------------
# Cache the variable values to allow setting a value externally.
set(_minimum_cxx_standard "11")
set(CMAKE_CXX_STANDARD "${_minimum_cxx_standard}" CACHE STRING "C++ standard")
if("${CMAKE_CXX_STANDARD}" LESS "${_minimum_cxx_standard}")
  message(FATAL_ERROR "CMAKE_CXX_STANDARD must be equal or larger than ${_minimum_cxx_standard}")
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON CACHE STRING "C++ standard required")
set(CMAKE_CXX_EXTENSIONS OFF CACHE STRING "C++ extensions")
message(STATUS "${_msg} - C++${CMAKE_CXX_STANDARD}")

#-----------------------------------------------------------------------------
project(SlicerCIP)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_NAME "Chest_Imaging_Platform")
set(EXTENSION_HOMEPAGE "https://chestimagingplatform.org/")
set(EXTENSION_CATEGORY "Chest Imaging Platform")
set(EXTENSION_STATUS "Alpha")
set(EXTENSION_CONTRIBUTORS "Applied Chest Imaging Laboratory, Brigham and Women's Hospital")
set(EXTENSION_DESCRIPTION "Chest Imaging Platform is an extension for quantitative CT imaging biomarkers for lung diseases. This work is funded by the National Heart, Lung, And Blood Institute of the National  Institutes of Health under Award Number R01HL116931. The content is solely the responsibility of the authors and does not necessarily represent the official views of the National Institutes of Health.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/acil-bwh/SlicerCIP/master/Resources/SlicerCIPLogo.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/acil-bwh/SlicerCIP/master/Resources/Screenshot1.png https://raw.githubusercontent.com/acil-bwh/SlicerCIP/master/Resources/Screenshot2.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

if (APPLE)
	# Force compiler because Slicer is also forcing it)
	set(CMAKE_C_COMPILER="/usr/bin/cc")
	set(CMAKE_CXX_COMPILER="/usr/bin/c++")
endif()


#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

if (NOT APPLE)
	set(CMAKE_C_COMPILER:FILEPATH=${Slicer_CMAKE_C_COMPILER})
	set(CMAKE_CXX_COMPILER:FILEPATH=${Slicer_CMAKE_CXX_COMPILER})
endif()

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#commented out to use vtklibxml2
#find_package(LibXml2 REQUIRED)
#mark_as_superbuild(LibXml2_DIR)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()


find_package(CIP REQUIRED)
include(${CIP_USE_FILE})

if(WIN32)
  add_definitions(-DUSE_STATIC_CIP_LIBS)
endif()

if(APPLE)
  #set(CMAKE_CXX_FLAGS "-stdlib=libstdc++ -mmacosx-version-min=10.6")
  set(CMAKE_SHARED_LINKER_FLAGS "-Wl,-dylib_file,/System/Library/Frameworks/OpenGL.framework/Versions/A/Libraries/libGL.dylib:/System/Library/Frameworks/OpenGL.framework/Versions/A/Libraries/libGL.dylib")
  set(CMAKE_EXE_LINKER_FLAGS "-Wl,-dylib_file,/System/Library/Frameworks/OpenGL.framework/Versions/A/Libraries/libGL.dylib:/System/Library/Frameworks/OpenGL.framework/Versions/A/Libraries/libGL.dylib")
endif()

#-----------------------------------------------------------------------------
set(CTK_COMPILE_PYTHON_SCRIPTS_GLOBAL_TARGET_NAME "SlicerCIP")

#-----------------------------------------------------------------------------
add_subdirectory(Scripted)
add_subdirectory(Loadable)

if(BUILD_TESTING)
#  add_subdirectory(Testing)
endif()

#-----------------------------------------------------------------------------
ctkFunctionAddCompilePythonScriptTargets(
  ${CTK_COMPILE_PYTHON_SCRIPTS_GLOBAL_TARGET_NAME})

#-----------------------------------------------------------------------------
#Package CIP into SlicerCIP build (CIP needs to be installed first before packaging extension)
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CIP_DIR};CIP;RuntimeLibraries;/")
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CIP_DIR};CIP;Runtime;/")

#Package entire extension build including cli-modules
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")

include(${Slicer_EXTENSION_CPACK})
