
include(SlicerMacroBuildScriptedModule)

#add_subdirectory(Example)
set(modules
  CIP_
  CIP_InteractiveLobeSegmentation
  CIP_ParenchymaAnalysis
  CIP_BodyComposition
  CIP_CalciumScoring
  CIP_LesionModel
  CIP_MIPViewer
  CIP_PAARatio
  CIP_PointsLabelling
  CIP_ParenchymaSubtypeTraining
  CIP_TracheaStentPlanning
  )

foreach (module ${modules})
  add_subdirectory(${module})
endforeach()



