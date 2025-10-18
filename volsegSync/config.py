#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : config.py
# Description : Volumen-Segmentation Sync - Settings management package.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>
#-------------------------------------------------------------------------------
import os
import configparser


VOLSEG_INSTANCE_DIRECTORY_NAME = ".volsegsync"
VOLSEG_INSTANCE_CFG_FILE_NAME = "config"
VOLSEG_INSTANCE_IDX_FILE_NAME = "index"
VOLSEG_INSTANCE_TAGS_FILE_NAME = "tags"


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
        print("[VolSegSync::load_config Exception] %s" % str(exception))


def save_config(config: configparser.ConfigParser, file_path: str):
    """
    Save settings into /.volsegsync/config file.
    """
    fp = open(file_path, 'w')
    config.write(fp)
    fp.close()
