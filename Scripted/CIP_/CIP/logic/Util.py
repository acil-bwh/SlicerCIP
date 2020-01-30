"""
Created on Oct 29, 2014
Common functions that can be useful in any Python module development
"""

import vtk
import sys
import traceback
import numpy as np
import SimpleITK as sitk
import subprocess

from . import file_conventions
from .geometry_topology_data import *

class Util: 
    # Constants
    OK = 0
    ERROR = 1

    file_conventions_extensions = file_conventions.file_conventions_extensions

    ###########
    # GENERAL SYSTEM FUNCTIONS
    @staticmethod
    def print_last_exception():
        """ Print in console the debug information for the last Exception occurred
        :return:
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print ("*** EXCEPTION OCCURRED: ")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

    @staticmethod
    def get_cip_extension(file_type_key, include_file_extension=False):
        """ Get the extension of a type of file
        @param file_type_key: type of file file_type_key
        @param include_file_extension: include the file extension (ex: .nrrd)
        @return: extension
        """
        if file_type_key not in Util.file_conventions_extensions:
            raise Exception("Key not found: " + file_type_key)
        s = Util.file_conventions_extensions[file_type_key]
        if not include_file_extension:
            s = os.path.splitext(s)[0]
        return s

    @staticmethod
    def get_case_name_from_labelmap(labelmap_name):
        """ Get the case name from a labelmap
        @param labelmap_name:
        @return: case name
        """
        if labelmap_name:
            ext = labelmap_name.split("_")[-1]
            return labelmap_name.replace("_" + ext, "")

    @staticmethod
    def get_dimensions(vtk_mrml_volume_node):
        """ Return a list of 3 positions with the dimensions of the volume (XYZ)
        :param vtk_mrml_volume_node: vtkMRMLVolumeNode or any subclass
        :return: list of 3 integer positions
        """
        # Get bounds in RAS format
        bounds = [0,0,0,0,0,0]
        vtk_mrml_volume_node.GetRASBounds(bounds)
        # Convert the limits to IJK format
        rastoijk=vtk.vtkMatrix4x4()
        vtk_mrml_volume_node.GetRASToIJKMatrix(rastoijk)
        bounds = [bounds[0],bounds[2],bounds[5], 1]
        dimensions = rastoijk.MultiplyPoint(bounds)
        return [int(round(dimensions[0])), int(round(dimensions[1])), int(round(dimensions[2]))]

    @staticmethod
    def is_windows():
        """ Current system platform is Windows based
        :return:
        """
        return os.sys.platform == "win32"

    @staticmethod
    def get_current_username():
        """ Current username (login).
        @return: username or "Unknown" if there is any problem
        """
        try:
            return os.path.split(os.path.expanduser('~'))[-1]
        except:
            return "Unknown"

    @staticmethod
    def create_directory(path):
        """ Create a directory if it does not exist yet and give the maximum permissions
        :param path: Full path of the directory
        :return: True if the directory was created or False if it already existed
        """
        if os.path.exists(path):
            return False
        os.makedirs(path)
        # Make sure that everybody has write permissions (sometimes there are problems because of umask)
        os.chmod(path, 0o777)
        return True

    @staticmethod
    def get_file_extension(file_path):
        """ Return the extension of a file (with the dot included)
        :param file_path: relative or absolute file path
        :return: extension with dot (ex: ".xml")
        """
        (f, ext) = os.path.splitext(file_path)
        return ext

    @staticmethod
    def vtkImageData_numpy_array(vtkImageData_node):
        """ Return a numpy array from a vtkImageData node
        :param vtkImageData_node:
        :return:
        """
        shape = list(vtkImageData_node.GetDimensions())
        shape.reverse()
        return vtk.util.numpy_support.vtk_to_numpy(vtkImageData_node.GetPointData().GetScalars()).reshape(shape)
        # shape = list(vtk_node.GetImageData().GetDimensions())
        # shape.reverse()
        # arr = vtk.util.numpy_support.vtk_to_numpy(vtk_node.GetPointData().GetScalars()).reshape(shape)
        # spacing = list(vtk_node.GetSpacing())
        # spacing.reverse()
        # origin = list(vtk_node.GetOrigin())
        # origin.reverse()
        # return arr, spacing, origin

    ##################
    # COORDINATE SYSTEMS
    @staticmethod
    def ras_to_ijk(volume_node, ras_coords, convert_to_int=True):
        """ Transform a list of RAS coords to IJK
        :param volume_node: vtk mrml scalar node
        :param ras_coords: list or array of RAS coordinates
        :param convert_to_int: return IJK coordinates as integer
        :return: list of IJK coordinates (xyz)
        """
        rastoijk=vtk.vtkMatrix4x4()
        volume_node.GetRASToIJKMatrix(rastoijk)
        cl = list(ras_coords)
        cl.append(1)
        l = list(rastoijk.MultiplyPoint(cl)[:-1])
        if convert_to_int:
            return [int(l[0]), int(l[1]), int(l[2])]
        return l

    @staticmethod
    def ijk_to_ras(volume_node, ijk_coords):
        """ Transform a list of IJK coords to RAS
        :return: list of RAS coordinates (xyz)
        """
        ijktoras=vtk.vtkMatrix4x4()
        volume_node.GetIJKToRASMatrix(ijktoras)
        cl = list(ijk_coords)
        cl.append(1)
        return list(ijktoras.MultiplyPoint(cl)[:-1])

    @staticmethod
    def __switch_ras_lps__(coords):
        """ Convert from RAS to LPS or viceversa (it is just flipping the first axis)
        :return: list of 3 coordinates
        """
        lps_to_ras_matrix = vtk.vtkMatrix4x4()
        lps_to_ras_matrix.SetElement(0, 0, -1)
        lps_to_ras_matrix.SetElement(1, 1, -1)

        cl = list(coords)
        cl.append(1)

        return list(lps_to_ras_matrix.MultiplyPoint(cl)[:-1])

    @staticmethod
    def ras_to_lps(coords):
        """ Convert coordinates from LPS to RAS
        :param coords:
        :return: list of 3 LPS coordinates
        """
        return Util.__switch_ras_lps__(coords)

    @staticmethod
    def lps_to_ras(coords):
        """ Convert coordinates from LPS to RAS
        :param coords:
        :return: list of 3 RAS coordinates
        """
        return Util.__switch_ras_lps__(coords)

    @staticmethod
    def get_lps_to_ijk_transformation_matrix(volume_node):
        """ Get the lps to ijk transformation matrix
        :param volume_node: vtkMRMLScalarNode
        :return:
        """
        matrix = vtk.vtkMatrix4x4()
        volume_node.GetRASToIJKMatrix(matrix)
        # Modify the required elements in RAS matrix to adapt it to LPS (flipping axis)
        # For that, we have to multiply with the diagonal matrix (-1, -1, 1, 1)
        id_matrix = vtk.vtkMatrix4x4()
        id_matrix.Identity()
        id_matrix.SetElement(0, 0, -1)
        id_matrix.SetElement(1, 1, -1)
        # Multiply
        result = vtk.vtkMatrix4x4()
        result.Multiply4x4(matrix, id_matrix, result)
        return result

    @staticmethod
    def itk_numpy_array(itk_image):
        """ From a ITK image, return:
        - Numpy array
        - Spacing
        - Origin
        :param itk_image: simple ITK image
        :return: tuple of values (array, spacing, origin)
        """
        arr = sitk.GetArrayFromImage(itk_image)
        itk_image = sitk.Image()
        return arr, itk_image.GetSpacing(), itk_image.GetOrigin()

    @staticmethod
    def itk_numpy_coordinate(itk_coordinate):
        """ Adapt a coordinate in ITK to a numpy array format handled by VTK (ie in a reversed order)
        :param itk_coordinate: coordinate in ITK (xyz)
        :return: coordinate in numpy (zyx)
        """
        l = list(itk_coordinate)
        l.reverse()
        return l

    @staticmethod
    def vtk_numpy_coordinate(vtk_coordinate):
        """ Adapt a coordinate in VTK to a numpy array format handled by VTK (ie in a reversed order)
        :param itk_coordinate: coordinate in VTK (xyz)
        :return: coordinate in numpy (zyx)
        """
        l = list(vtk_coordinate)
        l.reverse()
        return l

    @staticmethod
    def numpy_itk_coordinate(numpy_coordinate, convert_to_int=True):
        """ Adapt a coordinate in numpy to a ITK format (ie in a reversed order and converted to int type)
        :param numpy_coordinate: coordinate in numpy (zyx)
        :param convert_to_int: convert the coordinate to int type, needed for SimpleITK image coordinates
        :return: coordinate in ITK (xyz)
        """
        if convert_to_int:
            return [int(numpy_coordinate[2]), int(numpy_coordinate[1]), int(numpy_coordinate[0])]
        return [numpy_coordinate[2], numpy_coordinate[1], numpy_coordinate[0]]

    @staticmethod
    def numpy_vtk_coordinate(numpy_coordinate):
        """ Adapt a coordinate in numpy to a VTK format (ie in a reversed order)
        :param numpy_coordinate: coordinate in numpy (zyx)
        :return: coordinate in VTK (xyz)
        """
        l = list(numpy_coordinate)
        l.reverse()
        return l

    @staticmethod
    def convert_vtk_matrix_to_list(matrix):
        """ Convert a vtk matrix object into a list
        :param matrix: vtkMatrix4x4 or vtkMatrix3x3
        :return: list of elements with the same dimensions
        """
        if isinstance(matrix, type(vtk.vtkMatrix4x4())):
            dim = 4
        elif isinstance(matrix, type(vtk.vtkMatrix3x3())):
            dim = 3
        else:
            raise Exception("Type not allowed")
        threshold = 0.00000000000001    # Threshold for rounding
        result = []
        for i in range(dim):
            row = []
            for j in range(dim):
                n = matrix.GetElement(i, j)
                if abs(n) < threshold:
                    n = 0
                row.append(n)
            result.append(row)
        return result

    #########
    # OTHER FUNCTIONS
    @staticmethod
    def get_labelmap_slices(npArray):
        """ Get a dictionary with the slices where all the label data are contained in a numpy array
        representing a labelmap.
        The output will be a dictionary of [label_Code: array of slices]
        :param npArray: numpy array representing the image
        :return: dictionary of [label_Code: numpy array of slices]
        """
        # Extract labelmaps
        return Util.get_labelmap_slices_from_numpy_array(npArray)
    
    @staticmethod
    def get_labelmap_slices(np_array):
        """ Get a dictionary with the slices where all the label data are contained in a numpy array
        representing a labelmap.
        The output will be a dictionary of [label_Code: array of slices]
        Method 1: "2 steps" process compressing the array. It works much better when there are few slices with data
        :param np_array: numpy array representing the image
        :return: dictionary of [label_Code: numpy array of slices]
        """
        #start = time.clock()
        # Get an array with the slices that contain any data
        positions = np.where(np_array > 0)
        slices = np.unique(positions[0])
         
        # Build a new array just with the slices that contain data
        boundArray = np_array[slices,:,:]
         
        # Search for all the different label maps
        labelMaps = np.unique(boundArray)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the slices that contain the label
            s = np.where(boundArray == label)
            # "Translate" to the true slice numbers and store the result
            result[label] = slices[np.unique(s[0])] 
        
    #     end = time.clock()
    #     print ("get_labelmap_slices_from_numpy_array took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod 
    def get_labelmap_slices_2(np_array):
        """Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 2: without compressing the array using projections"""
        #start = time.clock()     
        # Search for all the different label maps
        labelMaps = np.unique(np_array)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the labelmaps with projections
            result[label] = Util.get_slices_for_label_from_numpy_array(np_array, label)
        
    #     end = time.clock()
    #     print ("get_labelmap_slices_from_numpy_array (method2) took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod 
    def get_labelmap_slices_3(np_array):
        """Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 3: without compressing the array using where (VERY SLOW!)"""
        #start = time.clock() 
         
        # Search for all the different label maps
        labelMaps = np.unique(np_array)
         
        result = {}    
        for label in (label for label in labelMaps if label>0):
            # Get the slices that contain the label
            s = np.where(np_array == label)
            # "Translate" to the true slice numbers and store the result
            result[label] = np.unique(s[0]) 
        
    #     end = time.clock()
    #     print ("get_labelmap_slices_from_numpy_array (method2) took {0} seconds".format(end-start))
         
        return result
    
    @staticmethod 
    def get_slices_for_label_from_numpy_array(np_array, label):
        """Get a numpyArray with the slices where label appears. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        """
        # Get an array with the slices that contain this label
        t = (np_array == label)
        # Make a double projection to get the slices that contain the label
        tproj = t.any(axis=1)
        tproj = tproj.any(axis=1)
         
        # Return the indexes of the slices with data
        return np.where(tproj)[0]

    @staticmethod
    def centroid(np_array, labelId=1):
        """ Calculate the coordinates of a centroid for a concrete labelId (default=1)
        :param np_array: numpy array
        :param labelId: label id (default = 1)
        :return: numpy array with the coordinates (int format)
        """
        mean = np.mean(np.where(np_array == labelId), axis=1)
        return np.asarray(np.round(mean, 0), np.int)


    @staticmethod
    def get_value_from_chest_type_and_region(chestType, chestRegion):
        """ Get an int code where the most significant byte encodes the ChestType and the less significant byte
        encodes the region
        @param chestType:
        @param chestRegion:
        @return: int code
        """
        return (chestType << 8) + chestRegion

    @staticmethod
    def openFile(filePath):
        """ Open a file with the default system application
        :param filePath: file to open
        """
        if os.sys.platform == "darwin":
            # MAC
            subprocess.call(["open", filePath])
        elif os.sys.platform == "win32":
            # Windows
            os.startfile(filePath)
        else:
            # Linux
            subprocess.call(["xdg-open", filePath])
