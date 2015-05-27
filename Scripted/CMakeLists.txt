
include(SlicerMacroBuildScriptedModule)

#add_subdirectory(Example)
set(modules
  #Example
  InteractiveLobeSegmentation
  LungRegistration
  ParenchymaAnalysis
  EmphysemaSubtypes
  CIP_Common
  CIP_BodyComposition
  CIP_GetImage
  PicasaSnap
  )

foreach (module ${modules})
  add_subdirectory(${module})
endforeach()



