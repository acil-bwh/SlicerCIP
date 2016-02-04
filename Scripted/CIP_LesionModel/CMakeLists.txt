#-----------------------------------------------------------------------------
set(MODULE_NAME CIP_LesionModel)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  FeatureExtractionLib/__init__
  FeatureExtractionLib/FirstOrderStatistics
  FeatureExtractionLib/GeometricalMeasures
  FeatureExtractionLib/MorphologyStatistics
  FeatureExtractionLib/ParenchymalVolume
  FeatureExtractionLib/RenyiDimensions
  FeatureExtractionLib/TextureGLCM
  FeatureExtractionLib/TextureGLRL
  FeatureWidgetHelperLib/__init__
  FeatureWidgetHelperLib/FeatureDescriptionLabel
  FeatureWidgetHelperLib/FeatureExtractionLogic
  FeatureWidgetHelperLib/FeatureWidgets
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  # add_subdirectory(Testing)
endif()

