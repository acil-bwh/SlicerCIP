
include(SlicerMacroBuildScriptedModule)

#add_subdirectory(Example)
set(modules
  CIP_InteractiveLobeSegmentation
  CIP_ParenchymaAnalysis
  CIP_Common
  CIP_BodyComposition
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



