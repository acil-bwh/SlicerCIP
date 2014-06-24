cmake_minimum_required(VERSION 2.8.9)

project(RegionType)

#-----------------------------------------------------------------------------
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/4.3/Extensions/RegionType")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Pietro Nardelli (UCC, SPL)")
set(EXTENSION_DESCRIPTION "This is an extension for selecting region/type from a chest labelmap")
set(EXTENSION_ICONURL "http://viewvc.slicer.org/viewvc.cgi/Slicer4/trunk/Extensions/Testing/RegionType/RegionType.png?revision=21746&view=co")
set(EXTENSION_SCREENSHOTURLS "http://wiki.slicer.org/slicerWiki/images/4/42/Slicer-r19441-RegionType-screenshot.png")

#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
add_subdirectory(MyRegionType)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
