#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : kernel.py
# Description : Segmentation Version Handler - Defs, data structs and core classes.
#
# Authors     : William A. Romero R.  <contact@waromero.com>,
#               Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------
import os
from dataclasses import dataclass
import SimpleITK as sitk

import config as cfg

from config import load_config
from commons import SegVerException
from exceptions import SegVerParserException
from manifest import (
    load_manifest,
    get_volume_seg_tuples
)

@dataclass
class SegVerTuple:
    """
    Volume-Segmentation data class.
    """
    index: int = -1
    name: str = "None"
    abs_vol_fpath: str = "None"
    abs_seg_fpath: str = "None"


class SegVerTListManager( object ):
    """
    VolSeg Tuple list manager.
    """
    def __init__( self ):
        """
        Default constructor.
        """
        self.__item = []
        self.__cidx = 0


    def add(self, item:SegVerTuple) -> None:
        """
        Add (Volume, Segmentation) Tuple object.
        """
        self.__item.append(item)


    def add_with( self, 
                  a_name:str,
                  a_vol_file_path:str,
                  a_seg_file_path:str ) -> None:
        """
        Add (Volume, Segmentation) item.
        """
        new_item = SegVerTuple()
        new_item.index = self.__cidx
        new_item.name =  a_name
        new_item.abs_vol_fpath = a_vol_file_path
        new_item.abs_seg_fpath = a_seg_file_path

        self.__item.append(new_item)
        self.__cidx += 1


    def get_vol_name_list( self ):
        """
        Return a list with the volume names.
        """
        name_list = []

        for volsegT in self.__item:
            name_list.append(volsegT.name)

        return name_list
        

    def get_tuple( self, index ):
        """
        Return i-th volsegT item.
        """
        volsegTuple = self.__item[index]

        return volsegTuple


    def get_volume_array( self, index ):
        """
        Return i-th volsegT item.
        """
        volsegTuple = self.__item[index]
        volume = sitk.ReadImage(volsegTuple.abs_vol_fpath)

        return sitk.GetArrayFromImage(volume)        


    def get_segmentation_array( self, index ):
        """
        Return i-th volsegT item.
        """
        volsegTuple = self.__item[index]
        segmentation = sitk.ReadImage(volsegTuple.abs_seg_fpath)

        return sitk.GetArrayFromImage(segmentation)        


class SegVerParser( object ):
    """
    SegVerHandler instance reader.
    """
    def __init__( self, inputDirectoryPath ):
        """
        Default constructor.
        """
        self.__working_directory = inputDirectoryPath
        self.__config_directory = os.path.join(self.__working_directory, cfg.SEGVER_INSTANCE_DIRECTORY_NAME)
        self.__config_file = os.path.join(self.__config_directory, cfg.SEGVER_INSTANCE_CFG_FILE_NAME)

        self.__name = "None"
        self.__description = "None"

        self.__volumes = []
        self.__segmentations = []
        self.__volSegTListManager = SegVerTListManager()       

        if not os.path.exists(self.__working_directory):
            raise SegVerException("[SegVerParser] No segVerHandler instance found in this directory.")
            
        if not os.path.exists(self.__config_file):
            raise SegVerException("[SegVerParser] No segVerHandler configuration found in this directory.")
        
        self.__load()


    def __str__( self ):
        """
        Default String obj.
        """
        outputStr = "\n[SegVerParser]\n\n"
        outputStr += "Instance: \n\t%s\n\n" % self.__working_directory
        outputStr += "Name: %s\n" % self.__name
        outputStr += "Description: %s\n" % self.__description

        return outputStr


    def __load( self ):
        """
        Load absolute file paths (volumes and segmentations).
        TODO: Manage/Use SegVerParserException.
        """
        try:
            cfg = load_config(self.__config_file)

            active_index = cfg['index']['active']
            manifest = load_manifest(self.__config_directory, active_index)

            self.__name = cfg["summary"]["name"]
            self.__description = cfg["summary"]["description"]

            vol_seg_tuples = get_volume_seg_tuples(manifest, self.__working_directory)

            for vol_seg in vol_seg_tuples:
                self.__volumes.append(vol_seg[1])
                self.__segmentations.append(vol_seg[2])
                self.__volSegTListManager.add_with(
                    vol_seg[0].rstrip(),
                    vol_seg[1],
                    vol_seg[2]
                )          

        except Exception as exception:
            print("[SegVerParser::Load Exception] %s" % str(exception))


    def get_volumes( self ):
        """
        Return volume's absolute file paths.
        """
        return self.__volumes
    

    def get_segmentations( self ):
        """
        Return segmentation's absolute file paths.
        """
        return self.__segmentations


    def get_SegVerTListManager( self ):
        """
        Return VolSeg Tuple List Manager instance.
        """
        return self.__volSegTListManager


    def get_name_list( self ):
        """
        Return a list with the names of idexed volumes.
        """
        return self.__volSegTListManager.get_vol_name_list()
