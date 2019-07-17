---
title: ECGButil
subtitle: ECG conversion and anonymization Batch utility
author: Daniel Loewenstein
version: 0.2.0
---

ECGButil
==========

Project overview
--------------------

ECGButil is an open source utility for easy batch conversion and anonymization
of electrocardiograms. ECGButil is developed in python and extends the
functionality of the 
[C# ECGToolkit](https://sourceforge.net/projects/ecgtoolkit-cs) developed by MJB
van Ettinger.

**Features**

* Batch conversion
  * Supported formats: MUSE-XML, SCP-ECG, DICOM, HL7 aECG, and ISHNE
* Anonymization using sha256 algorithm

Quick-start
-------------

Go to [releases](https://github.com/dloewenstein/ecgbutil/releases)
and download the .zip archive which contains the binaries.

1. Extract .zip archive
2. Run the executable ecgbutil.exe
3. Choose input folder with source ECG files
  * Make sure all ecg files are in the top level folder since subfolders are
    currently not supported
4. Choose output folder for converted/and/or/anonymized files
5. Press Convert

If option Anonymize is selected, the output will include `anonymization_key.csv`

| pat_id   | ano_id   | acq_datetime   | acg_datetime_ano   |
| :------: | :------: | :------------: | :----------------: |
|          |          |                |                    |

| variable         | description                                  |
| :-------:        | :----------:                                 |
| pat_id           | orginal patient ID                           |
| ano_id           | sha256 hashed patient ID                     |
| acq_datetime     | test acquistion datetime MM/DD/YYYY HH:MM:SS |
| acq_datetime_ano | sha256 hashed test acquisition datetime      |

License
--------

ECGButil is distributed under the
[Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)

Disclaimer of Warranty
---------------------------

ECGButil is provided on an AS IS BASIS, without warranties or conditions of any
kind. You are solely responsible for determining the appropriateness of using or
redistributing the software.

Issues
-------

Please report any issues or feature requests 
[here](https://github.com/dloewenstein/ecgbutil/issues)
