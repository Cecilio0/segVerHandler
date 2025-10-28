#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : exceptions.py
# Description : Segmentation Version Handler - App exceptions.  
#
# Authors     : Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------

class SegVerException(Exception):
    """
    Custom exception SegVerHandler errors.
    """
    pass

class ImageDataMatchingError(Exception):
    """
    Raised when two images do not have the same size, spacing, or orientation.
    """
    pass

class SegVerParserException( Exception ):
    """
    Custom exception class.
    """
    pass