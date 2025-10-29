#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : koms_service.py
# Description : Segmentation Version Handler - Kernel command business logic.
#
# Authors     : Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------

from datetime import datetime, timezone
import os
import click

from exceptions import SegVerException

from config import (
    load_config,
    save_config
)

from manifest import (
    build_empty_manifest,
    add_volume_version,
    remove_volume_version,
    get_all_version_strings,
    get_selected_version,
    set_selected_version,
    get_latest_version,
    save_manifest,
    load_manifest,
    get_volume_seg_tuples,
    remove_volume,
)

from commons import (
    extract_version_number,
    verify_volseg_match,
    update_index,
    validate_csv_path,
    check_geometry,
    hash_image
)


class KomsService:
    def initialize_instance(ctx, name, description, index_name, volumes, vext, segmentations, sext):
        """
        Initialize a new segVerHandler instance in the current directory.
        """

        segver_directory = ctx.obj["current_working_directory"]
        config_directory = ctx.obj["current_config_directory"]
        config_file_path = ctx.obj["current_config_file_path"]

        volumes_path = os.path.join(segver_directory, volumes)
        segmentations_path = os.path.join(segver_directory, segmentations)

        if os.path.isdir(config_directory) or os.path.isfile(config_file_path):
            raise SegVerException(f"\nA segVerHandler instance already exists in this directory.\n")
        
        _, warnings, errors, matches = verify_volseg_match(volumes_path, vext, segmentations_path, sext)

        if len(errors) > 0:
            log = [f"\nErrors were found during initialization. Please fix them and try again.\n"]
            return log, warnings, errors

        for warning_msg in warnings:
            click.echo(click.style(warning_msg, fg="yellow"))
            
        if len(warnings)>0 and not click.confirm('Do you want to continue?'):
            click.echo("segVerHandler is not initialized in this directory.")
            exit()

        try: 
            os.mkdir(config_directory)
        except Exception as exception:
            raise SegVerException(f"\nCould not create segVerHandler instance directory: {str(exception)}\n")

        cfg = load_config(config_file_path)
        cfg['summary']['name'] = name
        cfg['summary']['description'] = description
        cfg['index']['available'] = f'{index_name.strip()}'
        cfg['index']['active'] = index_name

        save_config(cfg, config_file_path)

        manifest = build_empty_manifest(
            index_name,
            volumes,
            vext,
            segmentations,
            sext
        )
        manifest["volumes"] = matches
        save_manifest(config_directory, manifest)

        log = [f"segVerHandler instance initialized in {segver_directory}"]

        return log, warnings, errors


    def __init__(self, ctx: click.Context):
        self._segver_directory = ctx.obj["current_working_directory"]
        self._config_directory = ctx.obj["current_config_directory"]
        self._config_file_path = ctx.obj["current_config_file_path"]

        if not os.path.isdir(self._config_directory) or not os.path.isfile(self._config_file_path):
            raise SegVerException(f"\nNo segVerHandler instance found in this directory.\n")

        self._config = load_config(self._config_file_path)

        self._active_index = self._config['index']['active']

        self._manifest = load_manifest(self._config_directory, self._active_index)

        self._ins_name = self._config['summary']['name']
        self._ins_description = self._config['summary']['description']
        self._available_indexes = self._config['index']['available'].split(',')


    def get_manifest(self):
        return self._manifest

    def get_active_index(self):
        return self._active_index
    
    def get_instance_description(self):
        return self._ins_description

    def get_instance_name(self):
        return self._ins_name
    
    def get_available_indexes(self):
        return self._available_indexes

    def get_segver_directory(self):
        return self._segver_directory


    def create_index(self, index_name, volumes, vext, segmentations, sext):
        log = []
        warnings = []
        errors = []

        if index_name in self._available_indexes:
            raise SegVerException(f"\nIndex '{index_name}' already exists. Available indexes: {', '.join(self._available_indexes)}\n")
        
        volumes_path = os.path.join(self._segver_directory, volumes)
        segmentations_path = os.path.join(self._segver_directory, segmentations)

        # Find matches for the new index
        log, warnings, errors, matches = verify_volseg_match(volumes_path, vext, segmentations_path, sext)

        manifest = build_empty_manifest(index_name, volumes, vext, segmentations, sext)
        manifest["volumes"] = matches

        self._manifest = manifest

        # Update the config to include the new index
        if self._config['index']['available']:
            self._config['index']['available'] += f",{index_name}"
        else:
            self._config['index']['available'] = index_name

        # Set the new index as active
        self._config['index']['active'] = index_name
        self._active_index = index_name

        log.append(f"Index '{index_name}' created and activated successfully.")

        return log, warnings, errors
    

    def rename_instance(self, new_name, new_description):
        log = []
        warnings = []
        errors = []

        if new_name != self._ins_name:
            log.append(f"{'Old name':>45} : {self._ins_name}")
            log.append(f"{'New name':>45} : {new_name}")
            self._config['summary']['name'] = new_name
            self._ins_name = new_name
        else: 
            log.append(f"{'Name':>45} : {self._ins_name} (unchanged)")

        if new_description != self._ins_description:
            log.append(f"{'Old description':>45} : {self._ins_description}")
            log.append(f"{'New description':>45} : {new_description}")
            self._config['summary']['description'] = new_description
            self._ins_description = new_description
        else: 
            log.append(f"{'Description':>45} : {self._ins_description} (unchanged)")

        save_config(self._config, self._config_file_path)

        return log, warnings, errors
    

    def update_index(self, new_manifest):
        log, warnings, errors, manifest = update_index(self._manifest, new_manifest)
        save_manifest(self._config_directory, manifest)
        return log, warnings, errors


    def get_volseg_matches(self):
        volumes_path, vext, segmentations_path, sext = self.__get_paths_and_exts()

        log, warnings, errors, matches = verify_volseg_match(volumes_path, vext, segmentations_path, sext)

        return log, warnings, errors, matches


    def export_index(self, output_csv_path):
        log = []
        warnings = []
        errors = []

        errors = validate_csv_path(output_csv_path)
        if len(errors) > 0:
            raise SegVerException(errors[0])

        volume_seg_tuples = get_volume_seg_tuples(self._manifest, self._segver_directory)

        if not volume_seg_tuples:
            raise SegVerException("No volumes found in the current index.")

        log.append(f"Exporting {len(volume_seg_tuples)} volume-segmentation pairs from index '{self._active_index}'.")

        try:
            with open(output_csv_path, 'w') as fp:
                fp.write("VOLUME FILE,SEGMENTATION FILE\n")
                for _, vfname, sfname in volume_seg_tuples:
                    fp.write(f"{vfname.rstrip()},{sfname.rstrip()}\n")
                fp.close()

            log.append(f"Exported to {output_csv_path}")
        except Exception as exception:
            raise SegVerException(f"Could not write to {output_csv_path}: {str(exception)}")

        return log, warnings, errors


    def link_segmentation(self, volume_fname, seg_fname):
        log = []
        warnings = []
        errors = []

        volumes_path, vext, segmentations_path, sext = self.__get_paths_and_exts()

        # Validate file extensions
        if not volume_fname.endswith(vext):
            errors.append(f"Volume file does not end with {vext}: {volume_fname}")
        if not seg_fname.endswith(sext):
            errors.append(f"Segmentation file does not end with {sext}: {seg_fname}")

        if len(errors) > 0:
            return log, warnings, errors

        volume_path = os.path.join(volumes_path, volume_fname)
        seg_path = os.path.join(segmentations_path, seg_fname)

        if not os.path.isfile(volume_path):
            errors.append(f"Volume file not found in volumes directory: {volume_path}")
        if not os.path.isfile(seg_path):
            errors.append(f"Segmentation file not found in segmentations directory: {seg_path}")

        if len(errors) > 0:
            return log, warnings, errors

        vol_base = volume_fname[:-len(vext)]
        seg_base = seg_fname[:-len(sext)]

        check_geometry(volume_path, seg_path)

        version = extract_version_number(seg_base, vol_base)
        if version is None:
            version = get_latest_version(self._manifest, vol_base)
            version = 1 if version is None else version + 1

        target_seg_path = os.path.join(segmentations_path, vol_base + "-v" + str(version) + sext)

        # Rename segmentation if basenames differ
        if target_seg_path != seg_path:
            if os.path.isfile(target_seg_path):
                errors.append(f"Target segmentation name already exists: {target_seg_path}")
            else:
                try:
                    os.rename(seg_path, target_seg_path)
                    seg_path = target_seg_path
                except OSError as e:
                    errors.append(f"Failed to rename segmentation: {e}")

        if len(errors) > 0:
            return log, warnings, errors

        added = add_volume_version(self._manifest, vol_base, f"v{version}", hash=hash_image(seg_path))
        save_manifest(self._config_directory, self._manifest)

        if added:
            log.append(f"Entry added to index.")
            log.append(f"\nAttached segmentation to volume:\n  Volume      : {volume_path}\n  Segmentation: {seg_path}\n  Basename    : {vol_base}\n")
        else:
            warnings.append(f"Segmentation file '{vol_base}' already present in index (nothing added).")

        return log, warnings, errors


    def select_segmentation(self, volume_fname, seg_version):
        log = []
        warnings = []
        errors = []

        # Basic validation of version token
        seg_version = seg_version.strip()
        if not seg_version.startswith('v') or not seg_version[1:].isdigit():
            errors.append(f"Version must be like v<N>: received '{seg_version}'")

        if len(errors) > 0:
            return log, warnings, errors

        volumes_path, vext, segmentations_path, sext = self.__get_paths_and_exts()

        # Validate volume filename & existence
        if not volume_fname.endswith(vext):
            errors.append(f"Volume file does not end with {vext}: {volume_fname}")
            return log, warnings, errors

        vol_base = volume_fname[:-len(vext)]
        expected_seg_fname = f"{vol_base}-{seg_version}{sext}"

        if vol_base not in self._manifest.get("volumes", {}):
            errors.append(f"Volume '{vol_base}' not found in manifest.")
            return log, warnings, errors

        volume_path = os.path.join(volumes_path, volume_fname)
        if not os.path.isfile(volume_path):
            errors.append(f"Volume file not found: {volume_path}")
            if vol_base in self._manifest.get("volumes", {}):
                remove_volume(self._manifest, vol_base)
                save_manifest(self._config_directory, self._manifest)
                errors.append(f"Removed volume '{vol_base}' from manifest.")
            return log, warnings, errors

        seg_path = os.path.join(segmentations_path, expected_seg_fname)

        old_selected = get_selected_version(self._manifest, vol_base)
        manifest_versions = get_all_version_strings(self._manifest, vol_base)

        if seg_version not in manifest_versions:
            errors.append(f"Version '{seg_version}' not found in manifest for volume '{vol_base}'.")
            errors.append("Please select from available versions: " + ", ".join(manifest_versions) + ".")
            warnings.append("No changes made to manifest.")
            return log, warnings, errors


        if not os.path.isfile(seg_path):
            errors.append(f"Segmentation file not found: {expected_seg_fname}")
            remove_volume_version(self._manifest, vol_base, seg_version)
            save_manifest(self._config_directory, self._manifest)
            errors.append(f"Removed version '{seg_version}' from manifest for volume '{vol_base}'.")
            manifest_versions = get_all_version_strings(self._manifest, vol_base)

            warnings.append("Please select from available versions: " + ", ".join(manifest_versions) + ".")
            if old_selected == seg_version:
                warnings.append(f"Previously selected version no longer available. Defaulting to version v{get_latest_version(self._manifest, vol_base)}")
            else:
                warnings.append("No changes made to manifest.")
            return log, warnings, errors


        set_selected_version(self._manifest, vol_base, seg_version)
        save_manifest(self._config_directory, self._manifest)

        if old_selected == seg_version:
            warnings.append(f"Selected version is already '{seg_version}' for volume '{vol_base}'.")
        else:
            log.append(f"Selected segmentation updated: {vol_base} -> {vol_base}-{seg_version}")

        return log, warnings, errors
    

    def update_segmentation_metadata(self, volume_fname, seg_version, seg_author, seg_notes, seg_tags):
        log = []
        warnings = []
        errors = []

        vol_base = volume_fname[:-len(self._manifest.get("volume-extension"))]

        if vol_base not in self._manifest.get("volumes", {}):
            errors.append(f"Volume '{vol_base}' not found in manifest.")
            return log, warnings, errors

        versions = self._manifest["volumes"][vol_base]["versions"]
        version_found = False
        changes_made = False
        for v in versions:
            if v["version"] == seg_version:
                if seg_author != "" and seg_author != v.get("author", ""):
                    log.append(f"{'Old author':>45} : {v.get("author", "")}")
                    log.append(f"{'New author':>45} : {seg_author}")
                    v["author"] = seg_author
                    changes_made = True
                else:
                    log.append(f"{'Author':>45} : {v.get("author", "")} (unchanged)")

                if seg_notes != "" and seg_notes != v.get("notes", ""):
                    log.append(f"{'Old notes':>45} : {v.get("notes", "")}")
                    log.append(f"{'New notes':>45} : {seg_notes}")
                    v["notes"] = seg_notes
                    changes_made = True
                else:
                    log.append(f"{'Notes':>45} : {v.get("notes", "")} (unchanged)")

                if seg_tags != "" and seg_tags != v.get("tags", []):
                    seg_tags = [tag.strip() for tag in seg_tags.split(',')]
                    log.append(f"{'Old tags':>45} : {v.get("tags", [])}")
                    log.append(f"{'New tags':>45} : {seg_tags}")
                    v["tags"] = seg_tags
                    changes_made = True
                else:
                    log.append(f"{'Tags':>45} : {v.get("tags", [])} (unchanged)")

                if changes_made == False:
                    log.append(f"No changes made to metadata for volume '{vol_base}', version '{seg_version}'.")
                else:
                    v["last-updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    log.append(f"{'Last updated':>45} : {v['last-updated']}")

                version_found = True
                break

        if not version_found:
            errors.append(f"Version '{seg_version}' not found for volume '{vol_base}'.")
            return log, warnings, errors
        
        log.append("")  # Blank line for readability

        self._manifest["volumes"][vol_base]["versions"] = versions
        save_manifest(self._config_directory, self._manifest)

        log.append(f"Metadata updated for volume '{vol_base}', version '{seg_version}'.")

        return log, warnings, errors


    def select_index(self, index_name):
        log = []
        warnings = []
        errors = []

        if index_name not in self._available_indexes:
            raise SegVerException(f"\nIndex '{index_name}' is not available. Available indexes: {', '.join(self._available_indexes)}\n")

        if index_name == self._active_index:
            log.append(f"Index '{index_name}' is already active.")
            return log, warnings, errors

        # Load the manifest for the new index, to ensure it is valid
        new_manifest = load_manifest(self._config_directory, index_name)

        # Update the config to set the new active index
        self._config['index']['active'] = index_name
        save_config(self._config, self._config_file_path)

        # Update internal state
        self._active_index = index_name
        self._manifest = new_manifest

        log.append(f"Index '{index_name}' activated successfully.")

        return log, warnings, errors
    

    def save_index(self):
        log = []
        warnings = []
        errors = []

        save_manifest(self._config_directory, self._manifest)

        save_config(self._config, self._config_file_path)

        log.append(f"Manifest for index '{self._active_index}' saved successfully.")

        return log, warnings, errors
    

    def __get_paths_and_exts(self):
        volumes_path = os.path.join(self._segver_directory, self._manifest.get("volume-path"))
        segmentations_path = os.path.join(self._segver_directory, self._manifest.get("label-path"))
        vext = self._manifest.get("volume-extension")
        sext = self._manifest.get("label-extension")
        return volumes_path, vext, segmentations_path, sext
