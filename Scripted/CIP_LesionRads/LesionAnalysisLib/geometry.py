""" Small, self-contained coordinate / centroid helpers used by CIP_Lesion.

These reproduce the behavior of the handful of functions the lesion-analysis path used
from the CIP framework (CIP.logic.Util), so that CIP_Lesion has no dependency on the CIP
package. The only intentional change versus the original is that ``centroid`` casts to a
plain Python ``int`` instead of the removed ``numpy.int`` alias.

Coordinate conventions:
  * VTK / ITK report image coordinates as (x, y, z).
  * numpy arrays obtained from Slicer volumes are indexed as (z, y, x).
So converting between the two is just reversing the order.
"""

import numpy as np


def centroid(labelmapArray, labelId=1):
    """ Centroid (z, y, x) of the voxels equal to ``labelId`` in a numpy labelmap array.

    :param labelmapArray: numpy array (z, y, x)
    :param labelId: label value to locate (default 1)
    :return: numpy array of rounded integer coordinates in (z, y, x) order
    """
    mean = np.mean(np.where(labelmapArray == labelId), axis=1)
    return np.round(mean).astype(int)


def vtk_numpy_coordinate(vtk_coordinate):
    """ (x, y, z) VTK/ITK coordinate -> (z, y, x) numpy coordinate (reversed). """
    c = list(vtk_coordinate)
    c.reverse()
    return c


def numpy_itk_coordinate(numpy_coordinate, convert_to_int=True):
    """ (z, y, x) numpy coordinate -> (x, y, z) ITK coordinate (reversed).

    :param convert_to_int: cast to int, required for SimpleITK image (seed) coordinates
    """
    if convert_to_int:
        return [int(numpy_coordinate[2]), int(numpy_coordinate[1]), int(numpy_coordinate[0])]
    return [numpy_coordinate[2], numpy_coordinate[1], numpy_coordinate[0]]
