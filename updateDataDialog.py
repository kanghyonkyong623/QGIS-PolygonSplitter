from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtSql import *

from qgis.core import *
from qgis.gui import *
from qgis.utils import iface

from dialogs import *
import copy
import xlrd
from ui_updateData import Ui_updateDataDlg

#global variable with short to full algorithm names

class updateDataDialog(QDialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.iface = iface
        self.ui = Ui_updateDataDlg()
        self.ui.setupUi(self)

        self.ui.frameEditToolbar.addAction(self.iface.actionToggleEditing())
        self.ui.frameEditToolbar.addAction(self.iface.actionSaveEdits())
        self.ui.frameEditToolbar.addAction(self.iface.actionAddFeature())
        self.ui.frameEditToolbar.addAction(self.iface.actionMoveFeature())
        self.ui.frameEditToolbar.addAction(self.iface.actionNodeTool())
        self.ui.frameEditToolbar.addAction(self.iface.actionDeleteSelected())
        self.ui.frameEditToolbar.addAction(self.iface.actionCutFeatures())
        self.ui.frameEditToolbar.addAction(self.iface.actionCopyFeatures())
        self.ui.frameEditToolbar.addAction(self.iface.actionPasteFeatures())
        self.ui.frameEditToolbar.setStyleSheet("background-color: rgb(229, 224, 255);");
        #self.ui.frameEditToolbar.setWindowFlags(Qt.ToolTip)
#         QObject.connect(self.ui.bStartEditing, SIGNAL("clicked"), self.iface.actionToggleEditing().activate(QAction.Trigger))
        self.ui.bStartEditing.clicked.connect(self.startEditingAction)
#         self.ui.bLoadExcel.clicked.connect(self.loadExcel)
        self.ui.bOk.clicked.connect(self.okClicked)
        self.ui.bCancel.clicked.connect(self.cancelClicked)
        self.ui.comLayers.currentIndexChanged.connect(self.selectLayer)
        #add layer in comboBox
        layerList = iface.mapCanvas().layers()
        for layer in layerList:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Point :
                self.ui.comLayers.addItem(layer.name())                
        
        QObject.connect(self.iface.mapCanvas(), SIGNAL("selectionChanged(QgsMapLayer *)"), self.selectFeature)
        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.attributeChanged)
        
        self.ui.table.setModel(self.model)
        self.ui.table.setColumnWidth(0, 200)
        self.ui.table.setColumnWidth(1, 160)
        header = QHeaderView(Qt.Horizontal)
        headerModel = QStandardItemModel()
        headerModel.setHorizontalHeaderLabels(["FieldName", "Value"])
        header.setModel(headerModel)
        self.ui.table.setHorizontalHeader(header)
        
        self.isEditing = False
        self.feature = QgsFeature()
        self.iface.actionToggleEditing().triggered.connect(self.changeEditMode)
        self.iface.currentLayerChanged.connect(self.changeBtnState)
        self.changeEditMode()
        self.changeBtnState()
        self.selectFeature(self.iface.mapCanvas().currentLayer())
    def attributeChanged(self, standardItem):
        name = self.model.item(standardItem.row()).text()
        self.feature.setAttribute(name, standardItem.text())
        self.iface.activeLayer().changeAttributeValue(self.feature.id(),
                                       self.feature.fieldNameIndex(name), standardItem.text())
#         self.iface.activeLayer().commitChanges()
        #QMessageBox.warning(self, standardItem.text(), attribute)
        pass
    
    def setModelEditable(self, editable):
        valueColumn = self.model.takeColumn(1)
        for item in valueColumn:
            item.setEditable(editable)
            
        self.model.appendColumn(valueColumn)
            
    def selectFeature(self, layer):
        if not layer: return
        nCount = layer.selectedFeatureCount()
        if nCount > 0 :
            if nCount > 1:
                QMessageBox.warning(self, str(nCount), "You can only edit one feature!")
                layer.removeSelection()
                layer.select(self.feature.id())
            self.feature = layer.selectedFeatures()[0]
            self.model.clear()
            self.readAttributes(self.feature)
            self.setModelEditable(layer.isEditable())
            
            #QMessageBox.warning(self, "test", msg)
        pass
    def readAttributes(self, feature):
        for field in feature.fields():
            try:
                name = field.name()
                attribute = str(feature.attribute(name))
    #             QMessageBox.warning(self, "name", attribute)
                stdItemName = QStandardItem(name)
                stdItemName.setEditable(False)
                
                stdItemValue = QStandardItem(attribute)
                stdItemValue.setEditable(self.iface.mapCanvas().currentLayer().isEditable())
                
                record = [stdItemName, stdItemValue]
                self.model.appendRow(record)
            except Exception, e:
                pass
                #QMessageBox.warning(self, "Exception", str(e))
        self.activateWindow()
        pass
    def startEditingAction(self):
        self.iface.actionToggleEditing().activate(QAction.Trigger)
        self.changeEditMode()
        
        
    def changeEditMode(self):
        if self.iface.mapCanvas().currentLayer():
            state = self.iface.mapCanvas().currentLayer().isEditable()
            self.iface.mapCanvas().currentLayer().setFeatureFormSuppress(QgsVectorLayer.SuppressOn)
            QObject.connect(self.iface.mapCanvas().currentLayer(), SIGNAL("featureAdded (QgsFeatureId)"), self.addedFeature)
            self.setModelEditable(self.iface.mapCanvas().currentLayer().isEditable())
            self.changeBtnState()
            
    def changeBtnState(self):
        if self.iface.mapCanvas().currentLayer() and self.iface.mapCanvas().currentLayer().isEditable() == True:
            self.ui.bStartEditing.setText("Stop Editing")
            # disable pop-up form after feature creation
        else:
            self.ui.bStartEditing.setText("Start Editing")

            
    def addedFeature(self, featureId):
        layer = self.iface.mapCanvas().currentLayer()
        layer.removeSelection()
        layer.select(featureId)
        self.selectFeature(layer)
        pass
    
    def okClicked(self):
        self.iface.mapCanvas().currentLayer().commitChanges()
        self.accept()
        
    def selectLayer(self):
        if self.ui.comLayers.count() < 1 :
            return

        layerList = self.iface.mapCanvas().layers()
        for layer in layerList:
            if layer.name() == self.ui.comLayers.currentText() :
                self.iface.setActiveLayer(layer)             
               
                return           

        
    def cancelClicked(self):
        self.reject()
