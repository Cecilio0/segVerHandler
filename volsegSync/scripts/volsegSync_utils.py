#!/usr/bin/python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name        : volsegSync_utils.py
# Description : volsegSync data manager / Proxy / interface. 
#
# Authors     : William A. Romero R.  <romero@creatis.insa-lyon.fr>
#                                     <contact@waromero.com>
#------------------------------------------------------------------------------
import os
import configparser
import traceback

VolSegSyn_CONFIG_DIRECTORY_NAME = ".volsegsync"
VolSegSyn_CONFIG_FILE_NAME = "config"
VolSegSyn_INDEX_FILE_NAME = "index"
VolSegSyn_TAGS_FILE_NAME = "tags"


class VolSegSynParser( object ):
    """
    VolSegSyn instance reader.
    """
    def __init__( self, inputDirectoryPath ):
        """
        Default constructor.
        """
        self.__working_directory = inputDirectoryPath
        self.__config_directory = os.path.join(self.__working_directory, VolSegSyn_CONFIG_DIRECTORY_NAME)
        self.__config_file_path = os.path.join(self.__config_directory, VolSegSyn_CONFIG_FILE_NAME)
        self.__index_file_path =  os.path.join(self.__config_directory, VolSegSyn_INDEX_FILE_NAME)

        self.__name = "None"
        self.__description = "None"

        self.__volumes = []
        self.__segmentations = []        

        if not os.path.exists(self.__working_directory):
            print("[CMRSegTools] No volsegSync instance found in this directory.")
            return None
            
        if not os.path.exists(self.__config_file_path):
            print("[CMRSegTools] No volsegSync configuration found in this directory.")
            return None
        
        if not os.path.exists(self.__index_file_path):
            print(f"[CMRSegTools] No volsegSync index found in this directory. {self.__index_file_path}")
            return None
        
        self.__Load()


    def __str__( self ):
        """
        Default String obj.
        """
        outputStr = "\n[VolSegSynParser]\n\n"
        outputStr += "Instance: \n\t%s\n\n" % self.__working_directory
        outputStr += "Name: %s\n" % self.__name
        outputStr += "Description: %s\n" % self.__description

        return outputStr


    def __Load( self ):
        """
        Load absolute volumes and segmentations file paths.
        """
        try:
            config = configparser.ConfigParser()
            config.read( self.__config_file_path )

            self.__name = config["summary"]["name"]
            self.__description = config["summary"]["description"]

            volumes_dir = config["directories"]["volumes"]
            vext = config["extensions"]["volumes"]
            segmentations_dir = config["directories"]["segmentations"]
            sext = config["extensions"]["segmentations"]

            volumes_path = os.path.join(self.__working_directory, volumes_dir)
            segmentations_path = os.path.join(self.__working_directory, segmentations_dir)

            with open(self.__index_file_path) as index:
                for fname in index:
                    
                    vfname = fname.rstrip() + vext
                    sfname = fname.rstrip() + sext

                    self.__volumes.append( os.path.join(volumes_path, vfname) )
                    self.__segmentations.append( os.path.join(segmentations_path, sfname) )

        except Exception as exception:
            print("[VolSegSynParser::Load Exception] %s" % str(exception))
            print("[VolSegSynParser::Load Exception] %s" % str(traceback.format_exc()))


    def GetVolumes( self ):
        """
        Load absolute volumes file paths.
        """
        return self.__volumes
    

    def GetSegmentations( self ):
        """
        Return segmentations file paths.
        """
        return self.__segmentations   