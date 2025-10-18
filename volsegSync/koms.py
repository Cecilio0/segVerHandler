#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : koms.py
# Description : Volumen-Segmentation Sync - Kernel commands.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>
#-------------------------------------------------------------------------------
import os
import click

from koms_service import KomsService

from commons import VolSegException

import quickviewer as qview

#-------------------------------------------------------------------------------
# COMMAND: INIT
#-------------------------------------------------------------------------------
@click.command()
@click.option("--name", default='No name', prompt="Type the name of this volsegSync instance")
@click.option("--description", default='No description', prompt="Type a short description of this volsegSync instance")
@click.option("--index-name", default="index", prompt="Type the name of the index to create", show_default=True)
@click.option("--volumes", prompt="Type the name of the volumes directory")
@click.option("--vext", prompt="Please type the file extension used for volume files. (i.e. \'.nii.gz\' or \'.mha\')")
@click.option("--segmentations", prompt="Type the name of the segmentations directory")
@click.option("--sext", prompt="Please type the file extension used for segmentation files (i.e. \'.nii.gz\' or \'.seg.nrrd\')")
@click.pass_context
def init( ctx: click.Context, 
          name: str,
          description: str,
          index_name: str,
          volumes: str,
          vext:str,
          segmentations: str,
          sext:str ):
    """
    Initialize a new volsegSync instance in the current directory.
    """
    try:
        log, _, errors = KomsService.initialize_instance(ctx, name, description, index_name, volumes, vext, segmentations, sext)
        
        if len(errors) > 0:
            for error_msg in errors:
                click.echo(click.style(error_msg, fg="red"))
        
        click.echo(log[0])
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()


#-------------------------------------------------------------------------------
# COMMAND: CREATE-INDEX
#-------------------------------------------------------------------------------
@click.command()
@click.option("--index-name", default="index", prompt="Type the name of the index to create", show_default=True)
@click.option("--volumes", prompt="Type the name of the volumes directory")
@click.option("--vext", prompt="Please type the file extension used for volume files. (i.e. \'.nii.gz\' or \'.mha\')")
@click.option("--segmentations", prompt="Type the name of the segmentations directory")
@click.option("--sext", prompt="Please type the file extension used for segmentation files (i.e. \'.nii.gz\' or \'.seg.nrrd\')")
@click.pass_context
def create_index( ctx: click.Context,
          index_name: str,
          volumes: str,
          vext:str,
          segmentations: str,
          sext:str ):
    """
    Create a new index in an existing volsegSync instance.
    """
    try:
        service = KomsService(ctx)
        log, warnings, errors = service.create_index(index_name, volumes, vext, segmentations, sext)
        log.append("") # Add a newline for better output formatting

        if len(errors) > 0:
            for error_msg in errors:
                click.echo(click.style(error_msg, fg="red"))
            exit()

        for warning_msg in warnings:
            click.echo(click.style(warning_msg, fg="yellow"))
            
        if len(warnings)>0 and not click.confirm('Do you want to continue?'):
            click.echo("volsegSync is not initialized in this directory.")
            exit()

        log2, _, _ = service.save_index()
        log.extend(log2)

    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    if len(log) > 0:
        for log_msg in log:
            click.echo(click.style(log_msg, fg="green"))


#-------------------------------------------------------------------------------
# COMMAND: SUMMARY
#-------------------------------------------------------------------------------
@click.command()
@click.pass_context
def summary( ctx: click.Context ):
    """
    Print summary of active index.
    """    
    try:
        service = KomsService(ctx)

        ins_name = service.get_instance_name()
        ins_description = service.get_instance_description()
        ins_index = service.get_active_index()
        ins_available_indexes = service.get_available_indexes()

        manifest = service.get_manifest()
        ins_volumes = manifest.get("volume-path", "N/A")
        ins_vext = manifest.get("volume-extension", "N/A")
        ins_segmentations = manifest.get("label-path", "N/A")
        ins_sext = manifest.get("label-extension", "N/A")

        indexed = manifest.get("volumes", {})
        num_lines = len(indexed)

        click.echo("\nInstance Information:\n")

        click.echo(f"{'Name':>45} : {ins_name}")
        click.echo(f"{'Description':>45} : {ins_description}\n")
        click.echo(f"{'Active index':>45} : {ins_index}")
        click.echo(f"{'Available indexes':>45} : {ins_available_indexes}\n")
        click.echo(f"{'Volumes directory':>45} : {ins_volumes}")
        click.echo(f"{'Volume file extension':>45} : {ins_vext}")
        click.echo(f"{'Segmentations':>45} : {ins_segmentations}")
        click.echo(f"{'Segmentation file extension':>45} : {ins_sext}\n")
        click.echo(f"{'Number of (volume,segmentation) pairs indexed':>45} : {num_lines}\n")

    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()


#-------------------------------------------------------------------------------
# COMMAND: RENAME
#-------------------------------------------------------------------------------
@click.command()
@click.option("--name", prompt="Type the new name for this instance")
@click.option("--description", default="", prompt="(Optional) Type the new description for this instance", required=False)
@click.pass_context
def rename(ctx: click.Context, name, description):
    """
    Rename the instance and optionally update its description.
    If no description is provided, it remains unchanged.
    """
    try:
        service = KomsService(ctx)
        log, _, _ = service.rename_instance(name, description if description.strip() != "" else service.get_instance_description())

    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    if len(log) > 0:
        for log_msg in log:
            click.echo(click.style(log_msg, fg="green"))


#-------------------------------------------------------------------------------
# COMMAND: UPDATE
#-------------------------------------------------------------------------------
@click.command()
@click.pass_context
def update( ctx: click.Context ):
    """
    Update file index.
    """
    try:
        service = KomsService(ctx)
        log, warnings, errors, matches = service.get_volseg_matches()
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    if len(errors) > 0:
        for error_msg in errors:
            click.echo(click.style(error_msg, fg="red"))
        exit()

    for warning_msg in warnings:
        click.echo(click.style(warning_msg, fg="yellow"))
        
    if len(warnings)>0 and not click.confirm('Do you want to continue?'):
        click.echo("volsegSync is not initialized in this directory.")
        exit()

    try:
        log, warnings, errors = service.update_index({ "volumes": matches })
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    if (len(log) > 0):
        click.echo(click.style("New (volume, segmentation) files added and/or removed:", fg="yellow"))
        for msg in log:
            click.echo(click.style(f"\t{msg}", fg="yellow"))

        click.echo(f"\nvolsegSync instance updated.\n")
    else:
        click.echo(f"\nNothing to do!\n")


#-------------------------------------------------------------------------------
# COMMAND: EXPORT
#-------------------------------------------------------------------------------
@click.command()
@click.option("--output", prompt="Type the output file path (example: ./data/test/testing_data.csv)")
@click.pass_context
def export( ctx: click.Context, output: str ):
    """
    Export main index.
    """
    try:
        service = KomsService(ctx)
        log, _, _ = service.export_index(output)
        for log_msg in log:
            click.echo(click.style(log_msg, fg="green"))
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()


#-------------------------------------------------------------------------------
# COMMAND: DISPLAY
#-------------------------------------------------------------------------------
@click.command()
@click.pass_context
def display( ctx: click.Context ):
    """
    (Volume, Segmentation) visualisation using quickViewer.
    """
    try:
        service = KomsService(ctx)
        config_working_directory = service.get_volseg_directory()
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    app = qview.QuickViewer(config_working_directory)
    app.MainLoop()


#-------------------------------------------------------------------------------
# COMMAND: LINK
#-------------------------------------------------------------------------------
@click.command()
@click.option("--volume", "volume_fname", prompt="Type the volume file name (with extension)")
@click.option("--segmentation", "seg_fname", prompt="Type the segmentation file name (with extension)")
@click.pass_context
def link(ctx: click.Context, volume_fname: str, seg_fname: str):
    """
    Associate an existing segmentation to an existing volume.
    Both files must already be in the instance directories.
    Always checks geometry (size, spacing, origin, direction).
    If the segmentation has a different basename it will be renamed.
    """
    try:
        service = KomsService(ctx)
        log, warnings, errors = service.link_segmentation(volume_fname, seg_fname)
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    for error_msg in errors:
        click.echo(click.style(error_msg, fg="red"))

    for warning_msg in warnings:
        click.echo(click.style(warning_msg, fg="yellow"))

    for log_msg in log:
        click.echo(click.style(log_msg, fg="green"))

    
#-------------------------------------------------------------------------------
# COMMAND: SELECT-SEG
#-------------------------------------------------------------------------------
@click.command(name="select-seg")
@click.option("--volume", "volume_fname", prompt="Type the volume file name (with extension)")
@click.option("--version", "seg_version", prompt="Type the NEW selected segmentation version (e.g., v1, v2)")
@click.pass_context
def select_seg(ctx: click.Context, volume_fname: str, seg_version: str):
    """
    Set the selected segmentation version for a given volume in the manifest.
    It updates the manifest's "selected-version" field for the volume, showing
    a warning if the segmentation file does not exist alongside the list of
    available segmentations.
    """
    try:
        service = KomsService(ctx)
        log, warnings, errors = service.select_segmentation(volume_fname, seg_version)
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()
        
    for error_msg in errors:
        click.echo(click.style(error_msg, fg="red"))

    for warning_msg in warnings:
        click.echo(click.style(warning_msg, fg="yellow"))

    for log_msg in log:
        click.echo(click.style(log_msg, fg="green"))

#-------------------------------------------------------------------------------
# COMMAND: SELECT-INDEX
#-------------------------------------------------------------------------------
@click.command(name="select-index")
@click.option("--index", "index_name", prompt="Type the name of the index to activate")
@click.pass_context
def select_index(ctx: click.Context, index_name: str):
    """
    Set the selected index for the volsegSync instance.
    """
    try:
        service = KomsService(ctx)
        log, warnings, _ = service.select_index(index_name)
    except VolSegException as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        exit()

    if len(warnings) > 0:
        for warning_msg in warnings:
            click.echo(click.style(warning_msg, fg="yellow"))

    if len(log) > 0:
        for log_msg in log:
            click.echo(click.style(log_msg, fg="green"))