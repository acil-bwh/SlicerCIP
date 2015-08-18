"""
Created on Oct 29, 2014
Common functions that can be useful in any Python module development
"""

#from __main__ import vtk
import vtk
import os, sys
import traceback
import numpy as np


class Util: 
    # Constants
    OK = 0
    ERROR = 1

    @staticmethod
    def print_last_exception():
        """ Print in console the debug information for the last Exception occurred
        :return:
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "*** EXCEPTION OCCURRED: "
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)
    
    @staticmethod
    def vtk_to_numpy_array(vtk_image_data):
        """Get a numpy array from a VTK image data volume.
        The order is: slice, row, column (Z,Y,X).
        UPGRADE: if we receive a vtkMRMLScalarVolumeNode (like a labelmap) we can now just invoke a = slicer.util.array(node.GetName()) 
        If we manipulate the array, the changes will reflect in the vtkNode calling node.GetImageData().Modified()
        """    
        shape = list(vtk_image_data.get_dimensions())
        shape.reverse()
        numpyarray = vtk.util.numpy_support.vtk_to_numpy(vtk_image_data.GetPointData().GetScalars()).reshape(shape)
        return numpyarray

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
    def get_file_extension(file_path):
        """ Return the extension of a file (with the dot included)
        :param file_path: relative or absolute file path
        :return: extension with dot (ex: ".xml")
        """
        (f, ext) = os.path.splitext(file_path)
        return ext

    @staticmethod 
    def get_labelmap_slices(vtk_image_data):
        """Get a dictionary with the slices where all the label data are contained.
        The output will be a dictionary of [label_Code: array of slices].
        The origin is a vktImageData node"""
        # Get a numpy array from the imageData
        npArray = Util.vtk_to_numpy_array(vtk_image_data)
        # Extract labelmaps
        return Util.get_labelmap_slices_from_numpy_array(npArray)
    
    @staticmethod
    def get_labelmap_slices_from_numpy_array(np_array):
        """Get a dictionary with the slices where all the label data are contained. The origin is a numpy array.
        Recall that the array will be read with Z,Y,X coordinates (because of the VTK conversion)
        Method 1: "2 steps" process compressing the array. It works much better when there are few slices with data"""
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
    def get_labelmap_slices_from_numpy_array_2(np_array):
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
    def get_labelmap_slices_from_numpy_array_3(np_array):
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
    def get_slices_for_label(vtk_image_data, label):
        """Return a numpy array with all the slices that contain the specified label. The origin is a vktImageData node"""
        # Get a numpy array from the imageData
        npArray = Util.vtk_to_numpy_array(vtk_image_data)
        # Get the results
        return Util.get_slices_for_label_from_numpy_array(npArray)
    
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
    def ras_to_ijk(volume_node, ras_coords):
        """ Transform a list of RAS coords to IJK
        :return: list of IJK coordinates (length 3)
        """
        rastoijk=vtk.vtkMatrix4x4()
        volume_node.GetRASToIJKMatrix(rastoijk)
        cl = list(ras_coords)
        cl.append(1)
        return list(rastoijk.MultiplyPoint(cl)[:-1])


    @staticmethod
    def ijk_to_ras(volume_node, ijk_coords):
        """ Transform a list of IJK coords to RAS
        :return: list of RAS coordinates (length 3)
        """
        ijktoras=vtk.vtkMatrix4x4()
        volume_node.GetIJKToRASMatrix(ijktoras)
        cl = list(ijk_coords)
        cl.append(1)
        return list(ijktoras.MultiplyPoint(cl)[:-1])


    @staticmethod
    def switch_ras_lps(coords):
        """ Convert from RAS to LPS or viceversa (it is just flipping the first two axis)
        :return: list of 3 RAS coordinates
        """
        return [-coords[0], -coords[1], coords[2]]


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
