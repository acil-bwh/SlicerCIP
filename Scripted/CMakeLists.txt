
include(SlicerMacroBuildScriptedModule)

#add_subdirectory(Example)
set(modules
  #Example
  InteractiveLobeSegmentation
  LungRegistration
  ParenchymaAnalysis
  EmphysemaSubtypes
  )

foreach (module ${modules})
  add_subdirectory(${module})
endforeach()



