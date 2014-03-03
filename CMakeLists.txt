cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerCIP)

# ------------------------------------------------------------------------
set(SLICERCIP_VERSION_MAJOR "0")
set(SLICERCIP_VERSION_MINOR "1")
set(SLICERCIP_VERSION_PATCH "0")
set(SLICERCIP_VERSION ${SLICERCIP_VERSION_MAJOR}.${SLICERCIP_VERSION_MINOR}.${SLICERCIP_VERSION_PATCH})


#-----------------------------------------------------------------------------
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/AirwayModule")
set(EXTENSION_CATEGORY "Chest Imaging Platform")
set(EXTENSION_CONTRIBUTORS "ACIL")
set(EXTENSION_DESCRIPTION "Potential extension module")
set(EXTENSION_ICONURL "http://viewvc.slicer.org/viewvc.cgi/Slicer4/trunk/Extensions/Testing/AirwayModule/AirwayModule.png?revision=21746&view=co")
set(EXTENSION_SCREENSHOTURLS "http://wiki.slicer.org/slicerWiki/images/4/42/Slicer-r19441-AirwayModule-screenshot.png")

#-----------------------------------------------------------------------------
project(SlicerCIP)

#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on via SuperBuild.cmake." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()


#-----------------------------------------------------------------------------
set(MODULE_NAME ${EXTENSION_NAME}) # Do not use 'project()'
set(MODULE_TITLE ${MODULE_NAME})

string(TOUPPER ${MODULE_NAME} MODULE_NAME_UPPER)

#-----------------------------------------------------------------------------
OPTION(SLICERCIP_ENABLE_EXPERIMENTAL_MODULES "Enable the building of work-in-progress, experimental modules." OFF)


#-----------------------------------------------------------------------------
add_subdirectory(Loadable)
add_subdirectory(Scripted)

if (SLICERCIP_ENABLE_EXPERIMENTAL_MODULES)
  #Add modules in development

endif()

if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()


#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
include(${Slicer_EXTENSION_CPACK})
