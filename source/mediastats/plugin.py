#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import ffprobe3
from pathlib import Path
from unmanic.libs.unplugins.settings import PluginSettings

# Configure plugin logger
logger = logging.getLogger("Unmanic.Plugin.mediastats")

class Settings(PluginSettings):
    settings = {"Cutoff": 1.0}

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__(*args, **kwargs)

def on_library_management_file_test(data):
    """
    Runner function - enables additional actions during the library management file tests.

    The 'data' object argument includes:
        library_id                      - The library that the current task is associated with
        path                            - String containing the full path to the file being tested.
        issues                          - List of currently found issues for not processing the file.
        add_file_to_pending_tasks       - Boolean, is the file currently marked to be added to the queue for processing.
        priority_score                  - Integer, an additional score that can be added to set the position of the new task in the task queue.
        shared_info                     - Dictionary, information provided by previous plugin runners. This can be appended to for subsequent runners.

    :param data:
    :return:
    
    """

    cutoff = Settings().get_setting('Cutoff')
    path = data.get('path')
    fsize = Path(path).stat().st_size
    probe = ffprobe3.probe(path)
    duration, height, width = None, None, None
    for stream in probe.streams:
        if stream.is_video():
            duration = stream.duration_secs
            height = stream.height
            width = stream.width
            break
    compression = fsize / (duration * height * width)
    if compression > cutoff:
        data['add_file_to_pending_tasks'] = True
    return data
