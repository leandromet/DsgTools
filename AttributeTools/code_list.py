# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                             -------------------
        begin                : 2015-11-23
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Brazilian Army - Geographic Service Bureau
        email                : suporte.dsgtools@dsg.eb.mil.br
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
import os

# Qt imports
from PyQt4 import QtGui, uic, QtCore
from PyQt4.QtCore import pyqtSlot, pyqtSignal

# QGIS imports
from qgis.core import QgsMapLayer, QgsField, QgsDataSourceURI
from PyQt4.QtGui import QTableWidgetItem, QMessageBox
from PyQt4.QtSql import QSqlDatabase, QSqlQuery

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'code_list.ui'))

class CodeList(QtGui.QDockWidget, FORM_CLASS):
    def __init__(self, iface):
        """Constructor."""
        super(CodeList, self).__init__()
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.iface = iface
          
        self.iface.currentLayerChanged.connect(self.setState)
          
        self.setState()
        
    @pyqtSlot()
    def setState(self):
        '''
        Sets the code list viewer initial state
        '''
        self.comboBox.clear()
        self.currLayer = self.iface.activeLayer()
        if not self.currLayer:
            return
        
        try:
            if QgsMapLayer is not None:
                if self.currLayer.type() != QgsMapLayer.VectorLayer:
                    return        
                for field in self.currLayer.pendingFields():
                    valueDict, keys = self.getCodeListDict(field.name())
                    if len(keys) > 0:
                        self.comboBox.addItem(field.name())
                self.comboBox.setCurrentIndex(0)
            
                self.loadCodeList()
        except:
            pass
                
    def getCodeListDict(self, field):
        '''
        Gets the code list dictionary
        '''
        fieldIndex = self.currLayer.fieldNameIndex(field)
        if fieldIndex == -1:
            return dict(), list()
        valueDict = self.currLayer.editorWidgetV2Config(fieldIndex) 
        keys = [value for value in valueDict.keys() if not (value == 'UseHtml' or value == 'IsMultiline')]
        return valueDict, keys
    
    def makeValueRelationDict(self, valueDict):
        '''
        Gets the value relation dictionary. This is necessary for multi valued attributes.
        '''
        ret = dict()

        codes = valueDict['FilterExpression'].replace('code in (', '').replace(')','').split(',')
        in_clause = ','.join(map(str, codes))
        keyColumn = valueDict['Key']
        valueColumn = valueDict['Value']
        table = valueDict['Layer'][:-17]#removing the date-time characters
        
        uri = QgsDataSourceURI(self.currLayer.dataProvider().dataSourceUri())
        if uri.host() == '':
            db = QSqlDatabase('QSQLITE')
            db.setDatabaseName(uri.database())
            sql = 'select code, code_name from dominios_%s where code in (%s)' % (table, in_clause)
        else:
            db = QSqlDatabase('QPSQL')
            db.setHostName(uri.host())
            db.setPort(int(uri.port()))
            db.setDatabaseName(uri.database())
            db.setUserName(uri.username())
            db.setPassword(uri.password())
            sql = 'select code, code_name from dominios.%s where code in (%s)' % (table, in_clause)
        
        if not db.open():
            db.close()
            return ret

        query = QSqlQuery(sql, db)
        if not query.isActive():
            QMessageBox.critical(self.iface.mainWindow(), self.tr("Error!"), self.tr("Problem obtaining domain values: ")+query.lastError().text())
            return ret
        
        while query.next():
            code = str(query.value(0))
            code_name = query.value(1)
            ret[code_name] = code
            
        db.close()
                
        return ret
        
    @pyqtSlot(int)
    def on_comboBox_currentIndexChanged(self):
        '''
        Slot that updates the code lists when the current active layers changes.
        '''
        self.loadCodeList()        
        
    def loadCodeList(self):
        '''
        Loads the current code lists viewer for the active layer
        '''
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels([self.tr('Value'), self.tr('Code')])
        
        field = self.comboBox.currentText()
        valueDict, keys = self.getCodeListDict(field)
        
        if 'FilterExpression' in keys:
            valueDict = self.makeValueRelationDict(valueDict)
            keys = valueDict.keys()

        self.tableWidget.setRowCount(len(keys))
        
        for row, value in enumerate(keys):
            code = valueDict[value]
            valueItem = QTableWidgetItem(value)
            codeItem = QTableWidgetItem(code)
            self.tableWidget.setItem(row, 0, valueItem)
            self.tableWidget.setItem(row, 1, codeItem)
        self.tableWidget.sortItems(1)