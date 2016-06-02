
include(SlicerMacroBuildScriptedModule)

#add_subdirectory(Example)
set(modules
  #Example
  CIP_InteractiveLobeSegmentation
  #LungRegistration
  #ParenchymaAnalysis
  #EmphysemaSubtypes
  CIP_Common
  CIP_BodyComposition
  # CIP_GetImage
  CIP_LesionModel
  CIP_MIPViewer
  CIP_PAARatio
  CIP_ParenchymaSubtypeTraining
  CIP_TracheaStentPlanning
  #PicasaSnap
  )

foreach (module ${modules})
  add_subdirectory(${module})
endforeach()



