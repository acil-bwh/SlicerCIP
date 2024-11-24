# SlicerCIP


Slicer extension for the Chest Imaging Platform

## Developers

### Build instructions

For a compilation of SlicerCIP you need to fork and compile 3D Slicer locally. This has to be done only once.  

#### Linux and Mac

set the SLICER_FOLDER variable, for instance to $HOME/slicer/SlicerRelease/Slicer-build

```
mkdir ../SlicerCIP-build
cd ../SlicerCIP-build
cmake -DCMAKE_CXX_STANDARD:STRING=17 -DCMAKE_BUILD_TYPE:STRING=Release -DSlicer_DIR=${SLICER_FOLDER}/SlicerRelease/Slicer-build ../SlicerCIP
make
```

#### Windows

Example: 

1. Fork 3D Slicer into "C:\D\S5\"
2. Build 3D Slicer into "C:\D\S5R\" 

then 

1. Fork this repository into "C:\D\" as "SlicerCIP"
2. Create a file "make_slicercip.bat" in "C:\D" folder with the following content: 

```
set startTime=%time%

mkdir "C:\D\SlicerCIP-build"
cd "C:\D\SlicerCIP-build"
cmake -DSlicer_DIR="C:\D\S5R\Slicer-build" "C:\D\SlicerCIP"

timeout /t 10

' must run this two times for unknown reasons to create SlicerCIP.sln

cmake -DSlicer_DIR="C:\D\S5R\Slicer-build" "C:\D\SlicerCIP"

echo Start Time: %startTime%
echo Finish Time: %time%

pause
```

3. Run "make_slicercip.bat" by double-clicking it
4. Open Visual Studio 2022
5. load "C:\D\SlicerCIP-build\SlicerCIP.sln"
6. build "ALL_BUILD"

### How to run your tests: 

Start 3D Slicer go -> "Edit" -> "Application settings" -> "Modules" -> "Additional module paths"

Include the following paths: 

```
C:/D/SlicerCIP-build/inner-build/lib/Slicer-5.1/cli-modules/Release
C:/D/SlicerCIP-build/inner-build/lib/Slicer-5.1/qt-scripted-modules
C:/D/SlicerCIP-build/inner-build/lib/Slicer-5.1/qt-loadable-modules/Release
```

Restart Slicer and test. 

### Run Example

${SLICER_FOLDER}/Slicer --additional-module-path ${PWD}/lib/Slicer-4.2/qt-loadable-modules --python-script ${PWD}/../SlicerCIP/Loadable/AirwayModule/Testing/Python/test_script.py

### Comments

- There is a hack in the vtkMRMLAirwayStorageNode::ReadDataInternal to copy the Hessians from the field data to the active tensors on the point data of the poly data. This should be revised after the format is verified
- The Hessians visualized should be inverted before given to the TensorGlyph visualization 
