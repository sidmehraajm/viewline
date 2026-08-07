"""
Copyright (c) 2026, Motion-Craft Technology All rights reserved.

Author:
    Subin. Gopi (subing85@gmail.com).

Module:
    ./widgets/playlist.py

Description:
    This module contains the primary playlist UI components used by the Review Player application.

Responsibilities:
    - Displaying project lists
    - Managing version/media playlists
    - Handling project switching
    - Displaying project thumbnails
    - Emitting media selection events
    - Providing playback interaction support

Main Components:
    PlaylistGroup:
        Main playlist container widget.

Features:
    - Project selection
    - Playlist browsing
    - Thumbnail preview support
    - Media open/play interaction
    - Signal-driven UI updates
    - Version/media list integration

Architecture:
    PlaylistWidget
        ↓
    ProjectsFrame
        ↓
    ProjectCombobox
        ↓
    User Project Selection
        ↓
    set_playlist()
        ↓
    Versions.get(project)
        ↓
    Version Collection
        ↓
    set_versions()
        ↓
    PlaylistTreewidget
        ↓
    PlaylistWidgetItem
        ↓
    User Selection
        ├── itemClicked
        │   ↓
        │   open_media()
        │   ↓
        │   select_media(False, context)
        │
        └── itemDoubleClicked
            ↓
            play_media()
            ↓
            select_media(True, context)

    ProjectsFrame
        ↓
    Projects.get()
        ↓
    Project Dataset
        ↓
    ProjectCombobox
        ↓
    User Project Selection
        ↓
    set_current_project()
        ↓
    ProjectIconLabel
        ↓
    project_changed Signal
        ↓
    Playlist Widget

Signals:
    project_changed:
        Emitted when the active project changes.

    select_media:
        Emitted when media items are clicked or double-clicked.
"""

from __future__ import absolute_import

import importlib

from PySide6 import QtCore
from PySide6 import QtWidgets

from viewline import scripts

from viewline.widgets.styles import WaitCursor
from viewline.widgets.labels import ProjectIconLabel

from viewline.widgets.layouts import VerticalLayout
from viewline.widgets.layouts import HorizontalLayout

from viewline.widgets.comboboxs import ProjectCombobox
from viewline.widgets.comboboxs import ShotCombobox
from viewline.widgets.comboboxs import TaskCombobox
from viewline.widgets.comboboxs import StatusFilterCombobox
from viewline.widgets.buttons import TextButton
from viewline.widgets.treewidgets import PlaylistTreewidget


class PlaylistWidget(QtWidgets.QWidget):
    """
    Main playlist container widget.

    This widget combines:

        - Project selector
        - Project thumbnail preview
        - Media/version playlist browser

    The playlist group acts as the central media browsing interface inside the Review Player application.

    Signals:
        project_changed (dict):
            Emitted when the active project changes.

        select_media (bool, dict):
            Emitted when a media item is clicked or double-clicked.

            Arguments:
                bool:
                    Playback state request.

                    - False = open media
                    - True = play media

                dict:
                    Media/version context.

    Example:
        >>> playlist = PlaylistGroup(parent, projects=data)
    """

    project_changed = QtCore.Signal(dict)
    select_media = QtCore.Signal(bool, dict)

    def __init__(self, parent, *args, **kwargs):
        """
        Initialize playlist widget.

        Args:
            parent (QtWidgets.QWidget):
                Parent widget.

            *args:
                Additional positional arguments.

            **kwargs:
                Optional keyword arguments.

                projects (list):
                    Project context list.
        """

        super(PlaylistWidget, self).__init__(parent)

        self.current_project = None

        # Main vertical layout
        self.verticallayout = VerticalLayout(self, space=5, margins=(0, 0, 0, 0))

        # Playlist tree widget (selectors now live in the top BrowserBar)
        self.playlistTreewidget = PlaylistTreewidget(self)
        self.verticallayout.addWidget(self.playlistTreewidget)

        # Connect playlist interactions
        self.playlistTreewidget.itemClicked.connect(self.open_media)
        self.playlistTreewidget.itemDoubleClicked.connect(self.play_media)

    def load(self, context):
        """
        Populate the version list from a BrowserBar load request.

        Args:
            context (dict):
                {"project": dict, "shot": dict|None,
                 "task": dict|None, "status": dict|None}
        """
        project = context.get("project")
        self.current_project = project

        with WaitCursor():
            importlib.reload(scripts)
            versions = scripts.Versions.get(
                project,
                context.get("shot"),
                context.get("task"),
                context.get("status"),
            )

        self.set_versions(versions)
        self.project_changed.emit(project)

    def set_versions(self, versions):
        """
        Populate playlist with versions/media items.

        Args:
            versions (list):
                Media/version context list.

        Example:
            >>> widget.set_versions(versions)
        """

        self.playlistTreewidget.setValues(versions)

    def open_media(self, widgetitem):
        """
        Emit media open request. Triggered when a playlist item is single-clicked.

        Args:
            widgetitem (PlaylistWidgetItem):
                Selected playlist item.
        """

        self.project_changed.emit(self.current_project)

        self.select_media.emit(False, widgetitem.context)

    def play_media(self, widgetitem):
        """
        Emit media playback request. Triggered when a playlist item is double-clicked.

        Args:
            widgetitem (PlaylistWidgetItem):
                Selected playlist item.
        """

        self.project_changed.emit(self.current_project)

        self.select_media.emit(True, widgetitem.context)


class BrowserBar(QtWidgets.QFrame):
    """
    Top selection bar: Project / Shot / Task / Status + Load.

    Lives above the viewer. Selecting a project cascades the shot, task and
    status dropdowns but does NOT load versions; the version list is only
    refreshed when the user presses Load.

    Signals:
        project_changed(dict):
            Emitted when the active project changes (for viewer/recaps context).

        load_requested(dict):
            Emitted on Load with {"project", "shot", "task", "status"}.
    """

    project_changed = QtCore.Signal(dict)
    load_requested = QtCore.Signal(dict)

    def __init__(self, parent, *args, **kwargs):
        super(BrowserBar, self).__init__(parent)

        self.current_project = None

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        self.setupUi()

    def setupUi(self):
        self.horizontallayout = HorizontalLayout(self, space=8, margins=(8, 6, 8, 6))

        # Project
        self.projectCombobox = ProjectCombobox(self, key="name")
        self.projectCombobox.setProjects()
        self.horizontallayout.addWidget(self.projectCombobox)

        # Shot (entity)
        self.shotCombobox = ShotCombobox(self, key="name")
        self.horizontallayout.addWidget(self.shotCombobox)

        # Task
        self.taskCombobox = TaskCombobox(self, key="name")
        self.horizontallayout.addWidget(self.taskCombobox)

        # Status filter
        self.statusCombobox = StatusFilterCombobox(self, key="code")
        self.horizontallayout.addWidget(self.statusCombobox)

        # Load button
        self.loadButton = TextButton(self, label="Load", toolTip="Load versions")
        self.loadButton.setMinimumWidth(80)
        self.horizontallayout.addWidget(self.loadButton)

        # Cascade only (no auto-load)
        self.projectCombobox.project_changed.connect(self.set_current_project)
        self.shotCombobox.shot_changed.connect(self._on_shot_changed)
        self.loadButton.clicked.connect(self._emit_load)

    def set_default_project(self, index=0):
        if not self.projectCombobox.contextList:
            return
        self.set_current_project(self.projectCombobox.contextList[index])

    def set_current_project(self, context):
        """Cascade shot/task/status dropdowns for the selected project."""
        self.current_project = context

        # Repopulate dependent dropdowns (signals blocked inside set* methods).
        self.shotCombobox.setShots(context)
        self.taskCombobox.setTasks(context, self.shotCombobox.getValue())
        self.statusCombobox.setStatuses(context)

        # Notify listeners (viewer clear, recaps status list) but do not load.
        self.project_changed.emit(context)

    def _on_shot_changed(self, shot):
        """Repopulate tasks for the selected shot (no load)."""
        self.taskCombobox.setTasks(self.current_project, shot)

    def _emit_load(self):
        if not self.current_project:
            return
        self.load_requested.emit(
            {
                "project": self.current_project,
                "shot": self.shotCombobox.getValue(),
                "task": self.taskCombobox.getValue(),
                "status": self.statusCombobox.getValue(),
            }
        )


if __name__ == "__main__":
    pass
