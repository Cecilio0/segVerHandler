#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : config.py
# Description : Segmentation Version Handler - Settings management package.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>,
#               Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------
import os
import configparser

from exceptions import SegVerException

SEGVER_INSTANCE_DIRECTORY_NAME = ".segverhandler"
SEGVER_INSTANCE_CFG_FILE_NAME = "config"
SEGVER_INSTANCE_IDX_FILE_NAME = "index"
SEGVER_INSTANCE_TAGS_FILE_NAME = "tags"


def load_config(file_path: str):
    """
    Load 'config' file settings.
    """
    config = configparser.ConfigParser()

    try:

        if os.path.exists(file_path):
            config.read(file_path)

        else:
            config["summary"] = { "name": "No name",
                                "description": "No description" }
            
            config["index"] = { "available": ["index"],
                                "active": "index" }

        return config
    
    except Exception as exception:
        raise SegVerException("Failed to load config")



def save_config(config: configparser.ConfigParser, file_path: str):
    """
    Save settings into /.segverhandler/config file.
    """
    fp = open(file_path, 'w')
    config.write(fp)
    fp.close()
