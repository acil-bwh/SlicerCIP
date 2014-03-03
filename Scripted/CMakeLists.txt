
include(SlicerMacroBuildScriptedModule)

set(modules
  Example
  )

foreach (module ${modules})
  add_subdirectory($modules)
endforeach()



