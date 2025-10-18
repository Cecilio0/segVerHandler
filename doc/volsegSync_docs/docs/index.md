# Welcome to volSegSync

A CLI tool for managing and synchronising volume – segmentation data pairs.

## Overview

Supervised learning–based segmentation methods rely on reference segmentations for training, meaning that the quality of the data used at this stage is crucial to the model’s performance.

The training data typically consist of two elements: the anatomical image and the segmentation of the structure of interest.

There is a one-to-one correspondence between an image and its segmentation; in other words, each segmentation is paired with exactly one image.

*volsegSync: Volume – Segmentation Synchronisation* is a CLI tool for managing and synchronising volume – segmentation data pairs. 


## Introduction

`volsegSync` is a command-line tool designed to streamline the management of paired volume and segmentation files in biomedical research workflows. It provides an interface for organising, validating, and synchronising (volume, segmentation) tuples across datasets and projects.

`volsegSync` supports consistent file pairing, batch operations, integrity checks, and integration with common data processing pipelines. This tool simplifies the complex task of keeping volumes and their segmentations reliably matched and organised.

### Key Features

- **Automated pairing**: Match volumes and segmentations by naming conventions or metadata.
- **Synchronisation**: Ensure consistency across datasets, folders, or remote storage.
- **Verification**: Detect missing or mismatched pairs.
- **Batch support**: Operate efficiently across large datasets.
- **Extensibility**: Integrate easily into existing shell scripts or data pipelines.

To begin using `volsegSync`, it is important to have a clear understanding of the naming conventions, versioning scheme, and index.

The following subsections provide a brief overview of the concepts required to get started with the tutorials.

### Naming convention standard

Consider the following file name:

```
C01-LowerBackFSE_T2w-D22061998.nii.gz
```

The file name may be divided into:

| Syntax | Description |
| ----------- | ----------- |
| Prefix | C01 |
| Basename | LowerBackFSE_T2w |
| Postfix | D22061998 |
| File extension | .nii.gz |


### Versioning scheme

A versioning scheme defines the rules and format used to create and assign unique identifiers to different versions of a file. For example, the following files use a sequential numbering scheme in the postfix:

```
C01-LowerBack_FSE_T2w_V133-D22061998-v1.nrrd
C01-LowerBack_FSE_T2w_V133-D22061998-v2.nrrd
C01-LowerBack_FSE_T2w_V133-D22061998-v3.nrrd
C01-LowerBack_FSE_T2w_V133-D22061998-v4.nrrd
```

### Index

An index defines the mapping between a volume (anatomical image) and a segmentation (label map).

```
C01-LowerBack_FSE_T2w_V001-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V001-D22061998.nrrd
C01-LowerBack_FSE_T2w_V002-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V002-D22061998.nrrd
C01-LowerBack_FSE_T2w_V003-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V003-D22061998.nrrd
C01-LowerBack_FSE_T2w_V004-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V004-D22061998.nrrd
C01-LowerBack_FSE_T2w_V005-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V005-D22061998.nrrd
.
.
.
C01-LowerBack_FSE_T2w_V133-D22061998.nii.gz -> C01-LowerBack_FSE_T2w_V133-D22061998.nrrd
```