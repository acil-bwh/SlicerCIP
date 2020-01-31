import SimpleITK as sitk
import numpy as np


class LungSplitter:
    def __init__(self, split_thirds=False):
        self.split_thirds = split_thirds
        
        self.size_th = 0.05
        self.coordinate_system = 'lps'
        # TODO: Chest conventions not available in Slicer. We hard coded the values for the labelmap!

        # c=ChestConventions()
        # self.RightLabel=c.GetChestRegionValueFromName('RightLung')
        # self.LeftLabel=c.GetChestRegionValueFromName('LeftLung')
        # self.WholeLung=c.GetChestRegionValueFromName('WholeLung')
        # self.UpperThird=c.GetChestRegionValueFromName('UpperThird')
        # self.MiddleThrid=c.GetChestRegionValueFromName('MiddleThird')
        # self.LowerThird=c.GetChestRegionValueFromName('LowerThird')
        # self.LeftUpperThird = c.GetChestRegionValueFromName('LeftUpperThird')
        # self.LeftMiddleThird= c.GetChestRegionValueFromName('LeftMiddleThird')
        # self.LeftLowerThrid = c.GetChestRegionValueFromName('LeftLowerThird')
        # self.RightUpperThird  = c.GetChestRegionValueFromName('RightUpperThird')
        # self.RightMiddleThrid = c.GetChestRegionValueFromName('RightMiddleThird')
        # self.RightLowerThrid  = c.GetChestRegionValueFromName('RightLowerThird')
        self.RightLabel = 2
        self.LeftLabel = 3
        self.WholeLung = 1
        self.UpperThird = 20
        self.MiddleThrid = 21
        self.LowerThird = 22
        self.LeftUpperThird = 9
        self.LeftMiddleThird = 10
        self.LeftLowerThrid = 11
        self.RightUpperThird = 12
        self.RightMiddleThrid = 13
        self.RightLowerThrid = 14

        self.cc_f = sitk.ConnectedComponentImageFilter()
        self.r_f = sitk.RelabelComponentImageFilter()
        self.ls = sitk.LabelShapeStatisticsImageFilter()

    def execute(self, lm):
        # Get Region/Type Information
        lm_np = sitk.GetArrayFromImage(lm)
        lm_region_np = lm_np & 255
        lm_type_np = lm_np >> 8

        # Work just on whole lung or Upper,Middle,Lower Thrids
        lm_wl_np = lm_region_np
        wl_mask=(lm_region_np == self.WholeLung) | (lm_region_np == self.UpperThird) |\
                 (lm_region_np == self.MiddleThrid) | (lm_region_np == self.LowerThird)

        if np.sum(wl_mask) == 0:
            # Nothing to do a filter should return the input lm
            return lm

        lm_wl_np[wl_mask] = self.WholeLung
        lm_wl = sitk.GetImageFromArray(lm_wl_np)
        lm_wl.CopyInformation(lm)

        # Output holder copy
        olm_tmp = sitk.Image(lm_wl)
        olm_np = sitk.GetArrayFromImage(olm_tmp)

        size = lm_wl.GetSize()

        # Axial run
        for zz in range(size[2]):
            cut = lm_wl[:, :, zz]
            out_cut = olm_np[zz, :, :]
            self.twoobject_label_cut(cut, out_cut, 2, zz, 0)

        # Coronal run
        for yy in range(size[1]):
            cut = lm_wl[:, yy, :]
            out_cut = olm_np[:, yy, :]
            self.twoobject_label_cut(cut, out_cut, 1, yy, 0)

        # Do majority voting split along sagittal
        for xx in range(size[0]):
            cut = lm_wl[xx, :, :]
            out_cut = olm_np[:, :, xx]
            self.allobjects_majority_voting_label_cut(cut,out_cut)

        # Splitting in Thirds
        if self.split_thirds is True:
            vol_right = np.sum(olm_np == self.RightLabel)
            vol_left = np.sum(olm_np == self.LeftLabel)
            target_vol_right = 0
            target_vol_left = 0
            for zz in range(size[2]):
                cut = olm_np[zz, :, :]
                right_mask = (cut == self.RightLabel)
                left_mask = (cut == self.LeftLabel)

                slice_vol_right = np.sum(right_mask)
                slice_vol_left = np.sum(left_mask)
                if target_vol_right <= vol_right/3:
                    cut[right_mask] = self.RightLowerThrid
                elif target_vol_right > vol_right/3 and target_vol_right <= 2*vol_right/3:
                    cut[right_mask] = self.RightMiddleThrid
                else:
                    cut[right_mask] = self.RightUpperThird

                target_vol_right = target_vol_right + slice_vol_right

                if target_vol_left <= vol_left/3:
                    cut[left_mask] = self.LeftLowerThrid
                elif target_vol_left > vol_left/3 and target_vol_left <= 2*vol_left/3:
                    cut[left_mask] = self.LeftMiddleThird
                else:
                    cut[left_mask] = self.LeftUpperThird

                target_vol_left = target_vol_left + slice_vol_left

        # Transfer type labels to output LM
        olm_np[np.logical_not(wl_mask)] = lm_region_np[np.logical_not(wl_mask)]
        olm_np = olm_np + (lm_type_np << 8)

        olm = sitk.GetImageFromArray(olm_np)
        olm.CopyInformation(lm)
        return olm

    def allobjects_majority_voting_label_cut(self, cut, out_np):
        cc = self.cc_f.Execute(cut)
        n_objects = self.cc_f.GetObjectCount()
        rr = self.r_f.Execute(cc)
        rr_np = sitk.GetArrayFromImage(rr)

        for oo in range(n_objects):
            out_np[rr_np == oo + 1]
            left_sum = np.sum(out_np[rr_np == oo + 1] == self.LeftLabel)
            right_sum = np.sum(out_np[rr_np == oo + 1] == self.RightLabel)
            if left_sum > right_sum:
                out_np[rr_np == oo + 1] = self.LeftLabel
            else:
                out_np[rr_np == oo + 1] = self.RightLabel

    def oneobject_majority_voting_label_cut(self, cut, out_np):
        cc = self.cc_f.Execute(cut)
        n_objects = self.cc_f.GetObjectCount()
        rr = self.r_f.Execute(cc)
        rr_np = sitk.GetArrayFromImage(rr)

        if n_objects == 1:
            out_np[rr_np == 1]
            left_sum = np.sum(out_np[rr_np == 1] == self.LeftLabel)
            right_sum = np.sum(out_np[rr_np == 1] == self.RightLabel)
            if left_sum > right_sum:
                out_np[rr_np == 1] = self.LeftLabel
            else:
                out_np[rr_np == 1] = self.RightLabel

    def twoobject_label_cut(self, cut, out_np, cutting_axis, cutting_idx, l_r_axis=0):
        # Detect and label components

        cc = self.cc_f.Execute(cut)
        n_objects = self.cc_f.GetObjectCount()

        if n_objects <= 1:
            # Leave mask untouch
            return
        else:
            rr = self.r_f.Execute(cc)
            self.ls.Execute(rr)
            vox_size = np.prod(rr.GetSpacing())
            cut_size = np.prod(rr.GetSize())
            total_area = cut_size * vox_size

            rr_np = sitk.GetArrayFromImage(rr)

            ss1 = np.sum(rr_np == 1)
            ss2 = np.sum(rr_np == 2)

            # Get Components that pass threshold
            if 1.0 * ss1 / cut_size > self.size_th and 1.0 * ss2 / cut_size > self.size_th:

                centroid1 = self.ls.GetCentroid(1)
                centroid2 = self.ls.GetCentroid(2)
                if centroid1[l_r_axis] > centroid2[l_r_axis]:
                    if self.coordinate_system == 'lps':
                        # Region 1 L and Region 2 R
                        out_np[rr_np == 1] = self.LeftLabel
                        out_np[rr_np == 2] = self.RightLabel
                    else:
                        out_np[rr_np == 1] = self.RightLabel
                        out_np[rr_np == 2] = self.LeftLabel
                else:
                    if self.coordinate_system == 'lps':
                        # Region 1 R and Region 2 L
                        out_np[rr_np == 1] = self.RightLabel
                        out_np[rr_np == 2] = self.LeftLabel
                    else:
                        out_np[rr_np == 1] = self.LeftLabel
                        out_np[rr_np == 2] = self.RightLabel
