# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                             -------------------
        begin                : 2019-10-10
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba.philipe@eb.mil.br
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


from qgis.PyQt.QtCore import QSettings, QObject

from qgis.core import QgsProject, Qgis


class ShortcutTool(QObject):
    def __init__(self, iface):
        """
        Hides or show active layers labels.
        """
        self.iface = iface
        super(ShortcutTool, self).__init__()
        self.actionList = []

    def addTool(self, manager, callback, parentToolbar, stackButton, iconBasePath):
        self.stackButton = stackButton
        icon_path = iconBasePath + "/on_off.png"
        toolTip = self.tr("DSGTools: Active Layer visibility")
        action = manager.add_action(
            icon_path,
            text=self.tr("DSGTools: Active Layer visibility"),
            callback=self.hideOrShowActiveLayer,
            add_to_menu=False,
            add_to_toolbar=False,
            withShortcut=True,
            tooltip=toolTip,
            parentButton=stackButton,
            isCheckable=False,
        )
        self.actionList.append(action)

        icon_path = iconBasePath + "/vertex.png"
        toolTip = self.tr("DSGTools: Toggle vertex's marker visibility")
        action = manager.add_action(
            icon_path,
            text=self.tr("DSGTools: Toggle vertex's marker visibility"),
            callback=self.hideOrShowMarkers,
            add_to_menu=False,
            add_to_toolbar=False,
            withShortcut=True,
            tooltip=toolTip,
            parentButton=stackButton,
            isCheckable=False,
        )
        self.actionList.append(action)

    def hideOrShowMarkers(self):
        try:
            self.stackButton.setDefaultAction(self.sender())
        except:
            pass
        qSettings = QSettings()
        qSettingsKey = (
            "digitizing/marker-only-for-selected"
            if Qgis.QGIS_VERSION_INT >= 33000
            else "qgis/digitizing/marker_only_for_selected"
        )
        currentState = qSettings.value(qSettingsKey)
        qSettings.setValue(qSettingsKey, not currentState)
        self.iface.mapCanvas().refresh()

    def hideOrShowActiveLayer(self):
        try:
            self.stackButton.setDefaultAction(self.sender())
        except:
            pass
        activeLayer = self.iface.activeLayer()
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        layerVisibilityState = activeLayer in layerTreeRoot.checkedLayers()
        layerTreeRoot.findLayer(activeLayer.id()).setItemVisibilityChecked(
            not layerVisibilityState
        )

    def unload(self):
        for action in self.actionList:
            try:
                self.iface.unregisterMainWindowAction(action)
            except:
                pass
