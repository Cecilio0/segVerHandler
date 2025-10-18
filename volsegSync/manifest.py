#!/usr/bin/python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name        : manifest.py
# Description : Volume-Segmentation Sync - Manifest management.
#
# Authors     : Daniel Restrepo Q. 
#-------------------------------------------------------------------------------

import os
import json
import hashlib
from datetime import datetime, timezone

DEFAULT_INDEX_NAME = "index"

# TODO: extract this logic
class VolSegException(Exception):
    """
    Custom exception VolSegSync errors.
    """
    pass

def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_instance_dir(root_dir: str) -> str:
    """
    Ensure the .volsegsync directory exists under root_dir.
    """
    if not os.path.isdir(root_dir):
        raise VolSegException(f"No volsegsync instance found in {root_dir}")
    return root_dir

# TODO: change with SimpleITK hash
def _hash_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def build_empty_manifest(index_name: str,
                         volume_path: str,
                         volume_extension: str,
                         label_path: str,
                         label_extension: str) -> dict:
    """
    Create a base manifest dictionary with no volumes populated.
    """
    return {
        "index-name": index_name,
        "volume-path": volume_path,
        "volume-extension": volume_extension,
        "label-path": label_path,
        "label-extension": label_extension,
        "volumes": {}
    }


def add_volume_version(manifest: dict,
                       subject_key: str,
                       version: str,
                       author: str = "",
                       notes: str = "",
                       tags=None,
                       ts: str | None = None,
                       last_updated: str | None = None) -> bool:
    """
    Add (or append) a version entry for a subject volume.
    subject_key example: 'sub-001_ses-01_T1w'
    """
    if tags is None:
        tags = []
    if subject_key not in manifest["volumes"]:
        manifest["volumes"][subject_key] = {
            "selected-version": version,
            "versions": []
        }

    ts_val = ts or _utc_iso()
    lu_val = last_updated or _utc_iso()
    version_id = f"{subject_key}-{version}"
    entry = {
        "id": version_id,
        "hash": _hash_string(version_id + ts_val),
        "ts": ts_val,
        "author": author,
        "notes": notes,
        "tags": tags,
        "version": version,
        "last-updated": lu_val
    }
    # If version exists, return False; else append and return True
    versions = manifest["volumes"][subject_key]["versions"]
    for i, v in enumerate(versions):
        if v["version"] == version:
            return False
    versions.append(entry)
    return True

def remove_volume(manifest: dict, subject_key: str):
    """
    Remove a subject volume entry from the manifest if it exists.
    """
    if subject_key in manifest["volumes"]:
        del manifest["volumes"][subject_key]

def remove_volume_version(manifest: dict, subject_key: str, version: str):
    """
    Remove a version entry for a subject volume if it exists.
    """
    log = ""
    if subject_key in manifest["volumes"]:
        versions = manifest["volumes"][subject_key]["versions"]
        manifest["volumes"][subject_key]["versions"] = [v for v in versions if v["version"] != version]
        # If the removed version was the selected-version, default to the latest version
        if get_selected_version(manifest, subject_key) == version:
            if versions:
                latest_version = f"v{get_latest_version(manifest, subject_key)}"
                set_selected_version(manifest, subject_key, latest_version)
                log = f"Updated selected-version for {subject_key} to latest version {latest_version}"
            else:
                set_selected_version(manifest, subject_key, None)
                log = f"Removed all versions for {subject_key}, no selected-version available"
        # If no versions remain, remove the entire subject entry
        if not manifest["volumes"][subject_key]["versions"]:
            del manifest["volumes"][subject_key]
        print(f"Removing version {version} from {subject_key}")

    return log

def get_latest_version(manifest: dict, subject_key: str) -> str | None:
    """
    Get the latest version string for a subject volume, or None if not found.
    """
    latest_version = None
    if subject_key in manifest["volumes"]:
        versions = manifest["volumes"][subject_key]["versions"]
        for v in versions:
            v_version = int(v.get("version", "")[1:])
            if latest_version is None or v_version > latest_version:
                latest_version = v_version
    return latest_version

def get_all_versions(manifest: dict, subject_key: str) -> list:
    """
    Get a list of all version objects for a subject volume, or empty list if not found.
    """
    if subject_key in manifest["volumes"]:
        return [v for v in manifest["volumes"][subject_key]["versions"]]
    return []

def get_all_version_strings(manifest: dict, subject_key: str) -> list:
    """
    Get a list of all version strings for a subject volume, or empty list if not found.
    """
    if subject_key in manifest["volumes"]:
        return [v["version"] for v in get_all_versions(manifest, subject_key)]
    return []

def get_selected_version(manifest: dict, subject_key: str) -> str | None:
    """
    Get the selected-version string for a subject volume, or None if not found.
    """
    if subject_key in manifest["volumes"]:
        return manifest["volumes"][subject_key].get("selected-version")
    return None

def set_selected_version(manifest: dict, subject_key: str, version: str):
    """
    Update the selected-version for a subject if it exists.
    """
    if subject_key in manifest["volumes"]:
        manifest["volumes"][subject_key]["selected-version"] = version


def save_manifest(root_dir: str, manifest: dict) -> str:
    """
    Save manifest to .volsegsync/<index-name>.manifest.json
    Returns the saved path.
    """
    inst_dir = _ensure_instance_dir(root_dir)
    index_name = manifest.get("index-name")
    out_path = os.path.join(inst_dir, f"{index_name}.manifest.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)
    return out_path


def load_manifest(root_dir: str, index_name: str) -> dict:
    """
    Load an existing manifest.
    """
    inst_dir = _ensure_instance_dir(root_dir)
    path = os.path.join(inst_dir, f"{index_name}.manifest.json")
    if not os.path.isfile(path):
        raise VolSegException(f"No volsegsync instance found in {root_dir}")
    with open(path, "r", encoding="utf-8") as fp:
        return json.load(fp)
    
def get_volume_seg_tuples(manifest: dict, root_dir: str) -> list:
    """
    Get a list of (volume_path, segmentation_path) tuples for all volumes in the manifest.
    """
    if not manifest or "volumes" not in manifest:
        return []
    
    volume_path = manifest.get("volume-path")
    label_path = manifest.get("label-path")
    volume_extension = manifest.get("volume-extension")
    label_extension = manifest.get("label-extension")
    
    vol_seg_pairs = []
    for subject_key in manifest["volumes"]:
        selected_version = get_selected_version(manifest, subject_key)
        if selected_version:
            vol_file = os.path.join(root_dir, volume_path, f"{subject_key}{volume_extension}")
            seg_file = os.path.join(root_dir, label_path, f"{subject_key}-{selected_version}{label_extension}")
            vol_seg_pairs.append((subject_key, vol_file, seg_file))

    return vol_seg_pairs