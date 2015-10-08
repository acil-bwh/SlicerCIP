import numpy as np
import SimpleITK as sitk
from CIP.logic import Util
from CIP.logic.SlicerUtil import *

markupsLogic = slicer.modules.markups.logic()
originalActiveListID = markupsLogic.GetActiveListID()
fiducialsNode = slicer.util.getNode(originalActiveListID)
activeNode = slicer.util.getNode("vtkMRMLScalarVolumeNode1")
spacing = activeNode.GetSpacing()
# pos0=np.array([0,0,0], np.float)
# pos1=np.array([0,0,0], np.float)
# pos2=np.array([0,0,0], np.float)
f0 = [0, 0, 0]
f1 = [0, 0, 0]
f2 = [0, 0, 0]
fiducialsNode.GetNthFiducialPosition(0, f0)
fiducialsNode.GetNthFiducialPosition(1, f1)
fiducialsNode.GetNthFiducialPosition(2, f2)
# pos0 = np.array(Util.ras_to_ijk(activeNode, f0), int)
# pos1 = np.array(Util.ras_to_ijk(activeNode, f1), int)
# pos2 = np.array(Util.ras_to_ijk(activeNode, f2), int)
pos0 = Util.ras_to_ijk(activeNode, f0)
pos0 = [int(pos0[0]), int(pos0[1]), int(pos0[2])]
pos1 = Util.ras_to_ijk(activeNode, f1)
pos1 = [int(pos1[0]), int(pos1[1]), int(pos1[2])]
pos2 = Util.ras_to_ijk(activeNode, f2)
pos2 = [int(pos2[0]), int(pos2[1]), int(pos2[2])]
# Get distance (use RAS coordinates to have in mind spacing)
dd01 = (
        (f0[0]-f1[0]) ** 2
        + (f0[1]-f1[1]) ** 2
        + (f0[2]-f1[2]) ** 2
        ) ** (1.0/2)

dd02 = (
        (f0[0]-f2[0]) ** 2
        + (f0[1]-f2[1]) ** 2
        + (f0[2]-f2[2]) ** 2
        ) ** (1.0/2)

dd12 = (
        (f2[0]-f1[0]) ** 2
        + (f2[1]-f1[1]) ** 2
        + (f2[2]-f1[2]) ** 2
        ) ** (1.0/2)

mean = (dd01 + dd02 + dd12) / 3
# d01 = np.linalg.norm(pos0 - pos1)
# d02 = np.linalg.norm(pos0 - pos2)
# d12 = np.linalg.norm(pos1 - pos2)
# itkpos0 = Util.numpy_itk_coordinate(pos0)
# itkpos1 = Util.numpy_itk_coordinate(pos1)
# itkpos2 = Util.numpy_itk_coordinate(pos2)
# d = (d01 + d02 + d02) / 3
npVolume = slicer.util.array(activeNode.GetID())
speedTest = (npVolume < -800).astype(np.int32)


# Create labelmap
lm = slicer.util.getNode("vtkMRMLLabelMapVolumeNode1")

lm01 = SlicerUtil.cloneVolume(activeNode, "lm01")
a01 = slicer.util.array("lm01")
lm02 = SlicerUtil.cloneVolume(activeNode, "lm02")
a02 = slicer.util.array("lm02")
lm12 = SlicerUtil.cloneVolume(activeNode, "lm12")
a12 = slicer.util.array("lm12")
result = SlicerUtil.cloneVolume(activeNode, "result")
resultArray = slicer.util.array("result")
lmresult = SlicerUtil.cloneVolume(lm, "lmresult")
lmresultArray = slicer.util.array("lmresult")


sitkImage = sitk.GetImageFromArray(speedTest)
fastMarchingFilter = sitk.FastMarchingImageFilter()
sitkImage.SetSpacing(spacing)

# Filter 01
d = dd01
# d=150
fastMarchingFilter.SetStoppingValue(d)
seeds = [pos0]
fastMarchingFilter.SetTrialPoints(seeds)
output = fastMarchingFilter.Execute(sitkImage)
outputArray = sitk.GetArrayFromImage(output)
a01[:] = 0
temp = outputArray <= d
a01[temp] = d - outputArray[temp]
lm01.GetImageData().Modified()

# Filter 02
d = dd02
# d=150
fastMarchingFilter.SetStoppingValue(d)
seeds = [pos2]
fastMarchingFilter.SetTrialPoints(seeds)
output = fastMarchingFilter.Execute(sitkImage)
outputArray = sitk.GetArrayFromImage(output)
a02[:] = 0
temp = outputArray <= d
a02[temp] = d - outputArray[temp]
lm02.GetImageData().Modified()

# Filter 12
d = dd12
fastMarchingFilter.SetStoppingValue(d)
seeds = [pos1]
fastMarchingFilter.SetTrialPoints(seeds)
output = fastMarchingFilter.Execute(sitkImage)
outputArray = sitk.GetArrayFromImage(output)
a12[:] = 0
temp = outputArray <= d
a12[temp] = d - outputArray[temp]
lm12.GetImageData().Modified()

# The solution is the intersection of the 3 labelmaps
scaleFactor = 4
inters = a01 + a02 + a12
resultArray[:] = inters * scaleFactor
result.GetImageData().Modified()

fix(mean*scaleFactor)

def fix(th):
    lmresultArray[:] = resultArray > th
    lmresult.GetImageData().Modified()



