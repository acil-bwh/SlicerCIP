SlicerCIP
=========

Slicer extension for the Chest Imaging Platform


Compilation
===========

1. set the SLICER_FOLDER variable, for instance to $HOME/slicer/Slicer4-SuperBuild/Slicer-build
2. mkdir ../SlicerCIP-build
3. cd ../SlicerCIP-build
4. cmake -DSlicer_DIR=${SLICER_FOLDER}/Slicer4-SuperBuild/Slicer-build ../SlicerCIP
5. make


Run Example
===========

${SLICER_FOLDER}/Slicer --additional-module-path ${PWD}/lib/Slicer-4.2/qt-loadable-modules --python-script ${PWD}/../SlicerCIP/Loadable/AirwayModule/Testing/Python/test_script.py


Comments
========

* There is a hack in the vtkMRMLAirwayStorageNode::ReadDataInternal to copy the Hessians from the field data to the active tensors on the point data of the poly data. This should be revised after the format is verified
* The Hessians visualized should be inverted before given to the TensorGlyph visualization 
