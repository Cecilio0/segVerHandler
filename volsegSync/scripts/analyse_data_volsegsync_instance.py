#!/usr/bin/python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name        : analyse_data_volsegsync_instance.py
# Description : Quick overview. 
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#------------------------------------------------------------------------------

import SimpleITK as sitk
import numpy as np

import os


from volsegSync_utils import VolSegSynParser


class ImageDataMatchingError(Exception):
    """
    Raised when two images do not have the same size, spacing, or orientation.
    """
    pass


def isImageDataMatching( referenceImage : sitk.Image,
                          targetImage : sitk.Image ) -> bool:
    """
    Check size, spacing, or orientation.
    """
        
    params = ""
    
    if referenceImage.GetSize() != targetImage.GetSize():
        params += "size,"
    
    if referenceImage.GetSpacing() != targetImage.GetSpacing():
        params += "spacing, "

    if referenceImage.GetOrigin() != targetImage.GetOrigin():
        params += "origin, "
    
    if referenceImage.GetDirection() != targetImage.GetDirection():
        params += "direction, "
    

    if len(params)>0:
        errorMessage = "The images differ in " + params + "please check!"
        raise ImageDataMatchingError(errorMessage)

    return True


if __name__ == "__main__":
    
    ROUND_DECIMALS = 3
           
    INPUT_VOLSEGSYNC_DIRECTORY_PATH="./volsegSync-data-weck_phantom-use_case_01"
       
    volsec_parser = VolSegSynParser( INPUT_VOLSEGSYNC_DIRECTORY_PATH )

    volumes = volsec_parser.GetVolumes()
    segmentations = volsec_parser.GetSegmentations()

    image_plane_data = {}
    bbox_data = {}

    for i in range (0, len(volumes) ):

        volume = sitk.ReadImage( volumes[i] )
        segmentation = sitk.ReadImage( segmentations[i] )
       
        volume_file_name = os.path.basename( volumes[i] )
        
        volume_size = volume.GetSize()
        volume_spacing = volume.GetSpacing()
        
        
        try:
            isImageDataMatching(volume, segmentation)
        except ImageDataMatchingError as e:
            print(e)
        
        pixel_spacing_cols = np.round(volume_spacing[0], ROUND_DECIMALS)
        pixel_spacing_rows = np.round(volume_spacing[1], ROUND_DECIMALS)
        slice_thickness = np.round(volume_spacing[2], ROUND_DECIMALS)
        
        ipd_pkey = str(pixel_spacing_cols) + "-" + str(pixel_spacing_cols) +  "-" + str(slice_thickness)
        
        
        if image_plane_data.get(ipd_pkey) is not None:
            image_plane_data[ipd_pkey] = image_plane_data[ipd_pkey] + 1
        else:
            image_plane_data[ipd_pkey] = 1
            

    print("{:^36} {:^9}".format("Pixel Spacing / Slice Thickness", "Number of volumes"))
    print("-"*56)
    for key, value in image_plane_data.items():        
        print("{:^36} {:^9}".format(key, value))
        
