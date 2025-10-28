#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : commons.py
# Description : SegVerHandler - Common functions.  
#
# Authors     : William A. Romero R.  <contact@waromero.com>,
#               Daniel Restrepo Q. <drones9182@gmail.com>,
#               Pablo Mesa H. <pablomesa08@gmail.com>
#-------------------------------------------------------------------------------
import os
import re
import SimpleITK as sitk
from datetime import datetime, timezone

from exceptions import SegVerException, ImageDataMatchingError

from manifest import (
    get_all_version_strings,
    get_all_versions,
    remove_volume,
    remove_volume_version
)


def find_differences(reference_list:list, target_list:list) -> tuple[list,list]:
    """
    Find 'only_in_reference' and 'only_in_target' elements.
    """
    reference_set = set(reference_list)
    target_set = set(target_list)

    only_in_reference = list(reference_set - target_set)
    only_in_target = list(target_set - reference_set)

    return only_in_reference, only_in_target


def find_outliers(reference_list:list, target_list:list, volumes_index:dict) -> tuple[list,list]:
    """
    Find 'only_in_reference' and 'only_in_target' elements.
    """
    reference_set = set(reference_list)
    target_set = set(target_list)

    # Check for outliers in the volumes index
    for vol_name, vol_data in volumes_index.items():
        if vol_name in reference_set:
            reference_set.remove(vol_name)
        for version in vol_data.get("versions", []):
            if version["id"] in target_set:
                target_set.remove(version["id"])

    return list(reference_set), list(target_set)


def search_files_in(directory:str, extension:str) -> tuple[list, int]:
    """
    Search files with 'extension' inside 'directory'.
    """
    output_fpaths = []
    output_fnames = []
    count = 0

    for dirpath, dirnames, filenames in os.walk(directory):
        for fname in filenames:

            if fname.endswith(extension):
                oname = fname[:-len(extension)]    
                filepath = os.path.join(dirpath, fname)

                output_fpaths.append(filepath)
                output_fnames.append(oname) # Only name.
                count += 1

    return(output_fpaths, output_fnames, count)


def verify_volseg_match( volumes_path:str, vext: str,
                         segmentations_path: str, sext: str ):
    """
    Identify disjunct elements between volumes and segmentations. 
    """
    log_messages = []
    warning_messages = []
    error_messages = []
    
    ref_fpaths = []
    ref_fnames = []
    ref_count = 0

    tar_fpaths = [] 
    tar_fnames = []
    tar_count = 0

    #---------------------------------------------------------------------------
    # VOLUMES
    #---------------------------------------------------------------------------
    if os.path.isdir(volumes_path):
        ref_fpaths, ref_fnames, ref_count = search_files_in(volumes_path, vext)
        if ref_count == 0:
            error_messages.append(f"\nDirectory {volumes_path} does not have any {vext} file!")
        else:
            log_messages.append(f"{ref_count} volumes found in {volumes_path}")

    else:
        error_messages.append(f"\nDirectory {volumes_path} does not exist!")

    #---------------------------------------------------------------------------
    # SEGMENTATIONS
    #---------------------------------------------------------------------------
    if os.path.isdir(segmentations_path):
        tar_fpaths, tar_fnames, tar_count = search_files_in(segmentations_path, sext)
        
        if tar_count == 0:
            error_messages.append(f"\nDirectory {segmentations_path} does not have any {sext} file!")
        else:
            log_messages.append(f"{tar_count} segmentations found in {segmentations_path}")
       
    else:
        error_messages.append(f"\nDirectory {segmentations_path} does not exist!")

    #---------------------------------------------------------------------------
    # MATCHES
    #---------------------------------------------------------------------------
    volumes_index = {}
    for vol_name in set(ref_fnames):
        versions = []
        for seg_base in tar_fnames:
            if not seg_base.startswith(vol_name + "-v"):
                continue

            ver_num = extract_version_number(seg_base, vol_name)
            if ver_num is None:
                continue

            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            versions.append({
                "id": seg_base,
                "hash": hash_image( os.path.join(segmentations_path, seg_base + sext) ),
                "ts": ts,
                "author": "",
                "notes": "",
                "tags": [],
                "version": f"v{ver_num}",
                "last-updated": ts
            })
        if versions:
            versions.sort(key=lambda x: int(x["version"][1:]))  # sort by numeric part
            volumes_index[vol_name] = {
                "selected-version": versions[-1]["version"],
                "versions": versions
            }

    #---------------------------------------------------------------------------
    # WITHOUT MATCH
    #---------------------------------------------------------------------------
    if ref_count > 0 and tar_count > 0:

        only_in_reference, only_in_target = find_outliers(ref_fnames, tar_fnames, volumes_index)

        if len(only_in_reference) > 0:
            vols_bereft_segs = "\nThe following files will not be included in the main tracking index!\n"
            vols_bereft_segs += "Volumes without segmentation: \n"

            for fname in only_in_reference:
                vols_bereft_segs += f"\t{fname}\n"

            warning_messages.append(vols_bereft_segs)

        if len(only_in_target) > 0:
            segs_bereft_vols = "\nThe following files will not be included in the main tracking index!\n"
            segs_bereft_vols += "Segmentations without volume: \n"

            for fname in only_in_target:
                segs_bereft_vols += f"\t{fname}\n"

            warning_messages.append(segs_bereft_vols)

    

    return log_messages, warning_messages, error_messages, volumes_index


def update_index(manifest: dict, new_manifest: dict):
    """
    Compares old manifest with new_manifest and updates old manifest in place.
    """
    log_messages = []
    warning_messages = []
    error_messages = []

    volume_set = set(manifest["volumes"].keys())
    new_volume_set = set(new_manifest["volumes"].keys())

    seg_set = set()
    for subject_key in manifest["volumes"].keys():
        for version in get_all_versions(manifest, subject_key):
            seg_set.add(version["id"])
            
    new_seg_set = set()
    for subject_key in new_manifest["volumes"].keys():
        for version in get_all_versions(new_manifest, subject_key):
            new_seg_set.add(version["id"])

    for subject_key, new_vol_data in new_manifest["volumes"].items():
        if subject_key not in manifest["volumes"]:
            manifest["volumes"][subject_key] = new_vol_data
            log_messages.append(f"Added new volume entry: {subject_key}")
            for version in new_vol_data["versions"]:
                log_messages.append(f"Added new segmentation {version['version']} to volume {subject_key}")
        else:
            existing_versions = get_all_version_strings(manifest, subject_key)
            for version in new_vol_data["versions"]:
                if version["version"] not in existing_versions:
                    manifest["volumes"][subject_key]["versions"].append(version)
                    log_messages.append(f"Added new segmentation {version['version']} to volume {subject_key}")

    # Identify removed volumes
    removed_volumes = volume_set - new_volume_set
    for subject_key in removed_volumes:
        remove_volume(manifest, subject_key)
        log_messages.append(f"Removed volume entry: {subject_key}")

    # Identify removed segmentations
    removed_segs = seg_set - new_seg_set
    for seg_id in removed_segs:
        for subject_key, vol_data in manifest["volumes"].items():
            version = extract_version_number(seg_id, subject_key)
            log = remove_volume_version(manifest, subject_key, f"v{version}")
            log_messages.append(f"Removed segmentation version {seg_id} from volume {subject_key}")
            if log: log_messages.append(log)

    return log_messages, warning_messages, error_messages, manifest


def validate_csv_path(file_path):
    """
    Verify the file for exporting data.
    """
    error_messages = []

    full_path = os.path.abspath(os.path.expanduser(file_path))

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)

    if not os.path.isdir(directory):
        error_messages.append(f"Directory does not exist: {directory}")

    if not filename.lower().endswith('.csv'):
        error_messages.append(f"File does not have a .csv extension: {filename}")

    return error_messages

def check_geometry(volume_path: str, seg_path: str):
    """
    Check if the geometry of the volume and segmentation images match.
    """
    vol_img = sitk.ReadImage(volume_path)
    seg_img = sitk.ReadImage(seg_path)
    diffs = []
    if vol_img.GetSize() != seg_img.GetSize(): diffs.append("size")
    if vol_img.GetSpacing() != seg_img.GetSpacing(): diffs.append("spacing")
    if vol_img.GetOrigin() != seg_img.GetOrigin(): diffs.append("origin")
    if vol_img.GetDirection() != seg_img.GetDirection(): diffs.append("direction")
    if diffs:
        raise ImageDataMatchingError(f"Geometry mismatch ({', '.join(diffs)}) between volume and segmentation.")

def extract_version_number(seg_base: str, vol_name: str) -> int | None:
    """
    Extract version string from segmentation base name.
    """
    m = re.match(rf'^{re.escape(vol_name)}-v(\d+)$', seg_base)
    if not m:
        return None
    return int(m.group(1))

def hash_image(fpath: str) -> str:
    """
    Generate a simple hash for a SimpleITK image based on its properties.
    """
    image = sitk.ReadImage(fpath)
    return sitk.Hash(image)