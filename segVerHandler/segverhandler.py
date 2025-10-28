#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : volsegsync.py
# Description : Volumen-Segmentation Sync - Main file.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>,
#               Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------
import os
import click

from config import  (
    SEGVER_INSTANCE_DIRECTORY_NAME,
    SEGVER_INSTANCE_CFG_FILE_NAME,
    SEGVER_INSTANCE_IDX_FILE_NAME )

import koms

@click.group()
@click.version_option()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Volumen-Segmentation Sync.
    """
    working_directory = os.getcwd()
    config_directory = os.path.join(working_directory, SEGVER_INSTANCE_DIRECTORY_NAME)
    config_file_path = os.path.join(config_directory,  SEGVER_INSTANCE_CFG_FILE_NAME)
    index_file_path = os.path.join( config_directory,  SEGVER_INSTANCE_IDX_FILE_NAME)

    ctx.ensure_object(dict)
    ctx.obj["current_working_directory"] = working_directory
    ctx.obj["current_config_directory"] = config_directory
    ctx.obj["current_config_file_path"] = config_file_path
    ctx.obj["current_index_file_path"] = index_file_path

cli.add_command(koms.init)
cli.add_command(koms.create_index)
cli.add_command(koms.summary)
cli.add_command(koms.rename)
cli.add_command(koms.update)
cli.add_command(koms.export)
cli.add_command(koms.display)
cli.add_command(koms.link)
cli.add_command(koms.select_seg)
cli.add_command(koms.select_index)