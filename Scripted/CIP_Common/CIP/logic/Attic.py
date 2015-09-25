# @staticmethod
# def meshgrid_3D(dim_z, dim_y, dim_x):
#     """ Get 3 matrixes to operate in a masked 3D space (see "meshgrid" function in numpy).
#     It assumes same size in the 3 dimensions (cube)
#     :param dim_z: length of the z dimension
#     :param dim_y: length of the y dimension
#     :param dim_x: length of the x dimension
#     :return: tuple with z, y, x meshgrid volumes
#     """
#     t1 = time.time()
#     ind0 = np.arange(dim_z)
#     ind1 = np.arange(dim_y)
#     ind2 = np.arange(dim_x)
#
#     try:
#         a, b, c = np.meshgrid(ind0, ind1, ind2)
#     except:
#         # Try "manual" way (3D introduced in numpy 1.8)
#         # Using numpy repetitions: about 7-8 seconds for a regular volume
#         # NOTE: Dimensions 0 and 1 are inverted to keep numpy meshgrid compatibility
#         t = np.repeat(ind0, dim_x)
#         t = t.reshape(dim_z, dim_x)
#         a = np.zeros([dim_y, dim_z, dim_x])
#         a[:, :, ind2] = t
#
#         t = np.repeat(ind1, dim_z)
#         b = np.repeat(t, dim_x)
#         b = b.reshape(dim_y, dim_z, dim_x)
#
#         c = np.zeros([dim_y, dim_z, dim_x], np.int)
#         c[ind1, :, :] = ind2
#
#         # Iterative version: more than 1 minute for a regular volume!
#         # a = np.zeros([dim_y, dim_z, dim_x], np.int)
#         # b = np.zeros([dim_y, dim_z, dim_x], np.int)
#         # c = np.zeros([dim_y, dim_z, dim_x], np.int)
#         # for i in range(dim_y):
#         #     for j in range(dim_z):
#         #         a[i, j:] = j
#         # for i in range(dim_y):
#         #     for j in range(dim_x):
#         #         b[i, :] = i
#         #         c[i, :, j] = j
#     t2 = time.time()
#     print("DEBUG: Time to build the meshgrid: {0} seconds".format(t2-t1))
#     return b, a, c      # For some reason numpy interchanges the first 2 dimensions...
#
#
#
# # @staticmethod
# # def get_sphere_mask_for_array(array, origin, radius, meshgrid=None):
# #     """ Get a bool numpy array that can work as a mask of the source array "drawing" a sphere of radius "radius"
# #     around a point "origin"
# #     :param array: original array
# #     :param origin: original point (3D tuple, list or array)
# #     :param radius: radius of the sphere
# #     :param meshgrid: 3-tuple with a meshgrid volume (3 volumes in total) of the same dimensions than "array" (in zyx format)
# #                     If this parameter is null, the meshgrid will be build here and it will be returned in the function
# #     :return: bool numpy array with the mask and a 3-tuple with the meshgrid built for this array (zyx)
# #     """
# #     if meshgrid is None:
# #         z, y, x = Util.meshgrid_3D(array.shape[0], array.shape[1], array.shape[2])
# #     else:
# #         z = meshgrid[0]
# #         y = meshgrid[1]
# #         x = meshgrid[2]
# #
# #     masc = np.zeros(array.shape, np.bool)
# #     masc[((origin[2]-x)**2) + ((origin[1]-y)**2) + ((origin[0]-z)**2) <= (radius**2)] = True
# #     return masc
#
# @staticmethod
# def get_distance_map_numpy(dims, spacing, origin, meshgrid=None):
#     """ Get a distance map from every position in the array to the specified origin, having in mind the spacing.
#     The distance is powered to square
#     :param dims: dimensions of the array (tuple, list, array...)
#     :param spacing: spacinf (tuple, list, array...)
#     :param origin: original point (tuple, list, array...)
#     :param meshgrid: 3-tuple with a meshgrid volume (3 volumes in total) of the same dimensions than "array" (in zyx format)
#                     If this parameter is null, the meshgrid will be built here
#     :return: numpy array with the distance map
#     """
#     if meshgrid is None:
#         z, y, x = Util.meshgrid_3D(dims[0], dims[1], dims[2])
#     else:
#         z = meshgrid[0]
#         y = meshgrid[1]
#         x = meshgrid[2]
#
#     #t1 = time.time()
#     distanceMap = (origin[2]-x)**2*spacing[2] + (origin[1]-y)**2*spacing[1] + (origin[0]-z)**2*spacing[0]
#     #t2 = time.time()
#     #print("DEBUG: Time to calculate the distance map (numpy): {0} seconds".format(t2-t1))
#     return distanceMap
#
#
# @staticmethod
# def get_distance_map_maurer(dims, spacing, origin):
#     """ Get a distance map from a particular point using ITK Maurer algorithm.
#     The distance is powered to square
#     It works much better than Danielson algorithms, but slower than Fast Marching
#     :param dims: list with the dimensions of the original volume (zyx)
#     :param spacing: list with the spacing of the original volume (zyx)
#     :param origin: list with the origin point (zyx)
#     :return: numpy array with the distance map
#     """
#     #t1 = time.time()
#     input = np.zeros(dims, np.byte)
#     input[origin[0], origin[1], origin[2]] = 1
#     image = sitk.GetImageFromArray(input)
#     image.SetSpacing(spacing)
#     filter = sitk.SignedMaurerDistanceMapImageFilter()
#     filter.SquaredDistanceOn()
#     filter.UseImageSpacingOn()
#     output = filter.Execute(image)
#     result = sitk.GetArrayFromImage(output)
#     #t2 = time.time()
#     # print("DEBUG: Time to calculate the distance map (maurer): {0} seconds".format(t2-t1))
#     return result
#
# @staticmethod
# def fast_marching_distance_map(dims, spacing, origin, stopping_value=None):
#     """ Get a distance map from a particular point using ITK FastMarching algorithm
#     :param dims: list with the dimensions of the original volume
#     :param spacing: list with the spacing of the original volume
#     :param origin: list with the origin point
#     :param stopping_value: max distance from the origin. The algorithm will stop when it reaches this distance (
#     the voxels not visited will have a +Infinite value)
#     :return: numpy array with the distance map
#     """
#     #t1 = time.time()
#     # Speed map (all ones because the growth will be constant)
#     input = np.ones(dims, np.int32)
#     image = sitk.GetImageFromArray(input)
#     # IMPORTANT: for ITK-numpy compatibility reasons, we have to reverse the spacing
#     spacingReversed = list(spacing)
#     spacingReversed.reverse()
#     image.SetSpacing(spacingReversed)
#     filter = sitk.FastMarchingImageFilter()
#     if stopping_value is not None:
#         filter.SetStoppingValue(stopping_value)
#     # For ITK compatibility reasons, we have to reverse the coordinates of the origin and convert to int
#     seeds = [[int(origin[2]), int(origin[1]), int(origin[0])]]
#     filter.SetTrialPoints(seeds)
#     output = filter.Execute(image)
#     result = sitk.GetArrayFromImage(output)
#     #t2 = time.time()
#     # print("DEBUG: Time to calculate the distance map (fast marching): {0} seconds".format(t2-t1))
#     return result
#
