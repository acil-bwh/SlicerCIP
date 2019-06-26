
include(SlicerMacroBuildScriptedModule)

set(modules
  CIP_
  CIP_AVRatio
  CIP_InteractiveLobeSegmentation
  CIP_ParenchymaAnalysis
  CIP_BodyComposition
  #CIP_CalciumScoring
  CIP_LesionModel
  CIP_MIPViewer
  CIP_PAARatio
  CIP_PointsLabelling
  CIP_ParenchymaSubtypeTraining
  CIP_TracheaStentPlanning
  CIP_ParenchymaSubtypeTrainingLabelling
  CIP_RVLVRatio
  CIP_Calibration
  )

foreach (module ${modules})
  add_subdirectory(${module})
endforeach()



