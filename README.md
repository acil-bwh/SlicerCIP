SlicerCIP
=========

Slicer extension for the Chest Imaging Platform


Compilation (Linux and Mac) 
===========

1. set the SLICER_FOLDER variable, for instance to $HOME/slicer/Slicer4-SuperBuild/Slicer-build
2. mkdir ../SlicerCIP-build
3. cd ../SlicerCIP-build
4. cmake -DSlicer_DIR=${SLICER_FOLDER}/Slicer4-SuperBuild/Slicer-build ../SlicerCIP
5. make

Compilation (Windows)
===========

For a Windows compilation of SlicerCIP you need to fork and compile 3D Slicer locally. This has to be done only once.  

Example usage: 

1. Fork 3D Slicer into "C:\D\S5\"
2. Build 3D Slicer into "C:\D\S5R\" 

then 

1. Fork this repository into "C:\Users\yourname\Documents\MySlicerExtensions" as "SlicerCIP"
2. Create a file "make_slicercip.bat" in "C:\Users\yourname\Documents\MySlicerExtensions" with the following content: 

		set startTime=%time%

		mkdir "C:\Users\yourname\Documents\MySlicerExtensions\SlicerCIP-build"
		cd "C:\Users\yourname\Documents\MySlicerExtensions\SlicerCIP-build"
		cmake -DSlicer_DIR="C:\D\S5R\Slicer-build" "C:\Users\yourname\Documents\MySlicerExtensions\SlicerCIP"

		timeout /t 10

		' must run this two times for unknown reasons to create SlicerCIP.sln

		cmake -DSlicer_DIR="D:\D\S5R\Slicer-build" "C:\Users\yourname\Documents\MySlicerExtensions\SlicerCIP"

		echo Start Time: %startTime%
		echo Finish Time: %time%

		pause
3. Run "make_slicercip.bat" by double-clicking it
4. Open Visual Studio 2022
5. load "C:\Users\yourname\Documents\MySlicerExtensions\SlicerCIP-build\SlicerCIP.sln"
6. build "ALL_BUILD"


Run Example
===========

${SLICER_FOLDER}/Slicer --additional-module-path ${PWD}/lib/Slicer-4.2/qt-loadable-modules --python-script ${PWD}/../SlicerCIP/Loadable/AirwayModule/Testing/Python/test_script.py


Comments
========

* There is a hack in the vtkMRMLAirwayStorageNode::ReadDataInternal to copy the Hessians from the field data to the active tensors on the point data of the poly data. This should be revised after the format is verified
* The Hessians visualized should be inverted before given to the TensorGlyph visualization 
