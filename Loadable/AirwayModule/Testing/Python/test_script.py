import vtkSlicerAirwayModuleModuleLogic
import os
import slicer
import urllib.request, urllib.parse, urllib.error

lg = vtkSlicerAirwayModuleModuleLogic.vtkSlicerAirwayModuleLogic()
lg.SetAndObserveMRMLScene(slicer.mrmlScene)

downloads = (
    (
        'http://slicer.kitware.com/midas3/download/item/116854',
        'airway_particles_acil.vtk',
        lg.AddAirway
    ),
)

for url, name, loader in downloads:
    filePath = slicer.app.temporaryPath + '/' + name
    if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print(('Requesting download %s from %s...\n' % (name, url)))
    urllib.request.urlretrieve(url, filePath)
    if loader:
        print(('Loading %s...\n' % (name,)))
    loader(filePath)
