from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore
import sys

from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from logindialog import loginDialog
from processing.core.Processing import Processing
from processing.gui.ProcessingToolbox import ProcessingToolbox
from processing.gui.HistoryDialog import HistoryDialog
from processing.gui.ConfigDialog import ConfigDialog
from processing.gui.ResultsDialog import ResultsDialog
from processing.modeler.ModelerDialog import ModelerDialog
# from processing.gui.CommanderWindow import CommanderWindow
from processing.modeler.ModelerAlgorithm import ModelerAlgorithm
from processing.modeler.WrongModelException import WrongModelException
from processing.gui.ParametersDialog import ParametersDialog
from processing.tools.system import *
from processing.modeler.ModelerUtils import ModelerUtils
from processing.modeler.Providers import Providers
from dialogs import *

from InsertTitleWnd import TitleWnd
from updateDataDialog import updateDataDialog

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class geoemergency(QObject):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        QObject.__init__(self)
        self.iface = iface
        
        self.reportsList = {}
        self.modelList = {}

    def initGui(self):
        QObject.connect(self.iface.actionOpenProject(), SIGNAL("triggered()"), self.setItemsDisable)
        QObject.connect(self.iface.actionOpenProject(), SIGNAL("triggered()"), self.loginNotify)
        QObject.connect(self.iface.actionOpenProject(), SIGNAL("triggered()"), self.initLists)
        QObject.connect(self, SIGNAL("loginNotify"), self.login)
        QObject.connect(self.iface.actionNewProject(), SIGNAL("triggered()"), self.initLists)
        QObject.connect(self.iface, SIGNAL("newProjectCreated()"), self.setItemsDisable)
        self.iface.composerAdded.connect(self.addReport)
#         self.toolbar = GeoEmergencyToolBar(self.iface)
#         self.toolbar.show()        
        self.qgsToolbar = self.iface.addToolBar("GeoEmergency")
        self.qgsToolbar.setWindowFlags(Qt.WindowTitleHint)
        
        # Log in action
        self.loginAction = self.qgsToolbar.addAction(QIcon(":/plugin/logo_241.png"), "Login")
        self.loginAction.triggered.connect(self.login)
        # Update Data
        self.updateDataAction = self.qgsToolbar.addAction("Update Data")
        self.updateDataAction.triggered.connect(self.updateData)
        
        # Create Report
        self.createReportAction = self.qgsToolbar.addAction("Create Report")
        self.createReportAction.triggered.connect(self.createReport)
        
        self.comboReports = QComboBox()
        self.qgsToolbar.addWidget(self.comboReports).setVisible(True)
        self.comboReports.setAutoFillBackground(False)
        self.comboReports.setStyleSheet(_fromUtf8("background-color: rgb(235, 235, 235);"))
        
        # Create Model
        self.createModelAction = self.qgsToolbar.addAction("Create Model")
        self.createModelAction.triggered.connect(self.openModeler)

        self.comboModels = QComboBox()
        self.qgsToolbar.addWidget(self.comboModels).setVisible(True)
        self.comboModels.setAutoFillBackground(False)
        self.comboModels.setStyleSheet(_fromUtf8("background-color: rgb(235, 235, 235);"))
        
        self.comboReports.currentIndexChanged.connect(self.selectReport)
        self.comboModels.currentIndexChanged.connect(self.runModel)

        # init toolbar status
        self.setItemsEnabled(False)
        self.qgsToolbar.setFixedHeight(40)
        
        self.initLists()
        # Init Models List 
        self.modelerDlg = None
        
    def setItemsEnabled(self, enabled):
        self.updateDataAction.setEnabled(enabled)
        self.createReportAction.setEnabled(enabled)
        self.comboReports.setEnabled(enabled)
        self.createModelAction.setEnabled(enabled)
        self.comboModels.setEnabled(enabled)

    def addModelsList(self):
        path = ModelerUtils.modelsFolder()
        fileName = "*.model"
        currentDir = QDir(path)        
        files = currentDir.entryList([fileName], QDir.Files | QDir.NoSymLinks)
        if (len(files) > 0):            
            for modelFileName in files:
                if modelFileName:
                    
                    try:
                        modelPath = path + "/" + modelFileName
                        file = QFile(modelPath)
                        if file.open(QFile.ReadOnly | QFile.Text) == False:
                            QMessageBox.warning(self.iface.mainWindow(), "Application",
                                                 "Cannot read file %s:\n%s." % 
                                                 (modelPath, file.errorString()))
                            return
                    
                        textFile = QTextStream(file)
                        strTemp = textFile.readLine()
                        algName = strTemp[5:]
                        self.modelList[algName] = modelPath
                        self.comboModels.addItem(algName)
                        
                    except WrongModelException, e:
                        QMessageBox.critical(self.iface.mainWindow(), 'Could not open model',
                                'The selected model could not be loaded.\n'
                                        'Wrong line: %s' % e.msg)
    def unload(self):
        # Remove the plugin menu item and icon
        # self.iface.removePluginMenu("Geo&Emergency",self.action)
        # self.iface.removeToolBarIcon(self.action)
        #del self.toolbar
        pass

    def updateData(self):
        
        dlg = updateDataDialog(self.iface)
        dlg.show()
        dlg.exec_()
        
    def createReport(self):
        dlg = TitleWnd()
        result = dlg.exec_()
        
        if (result == 1):
            report = self.iface.createNewComposer(dlg.title)            

    def selectReport(self):
        if len(self.reportsList) < 1 or self.comboReports.currentIndex() < 1:
            return
#         QMessageBox.warning(self.iface.mainWindow(), "test", "test")
        report = self.reportsList[self.comboReports.currentText()]
        if report and report.composerWindow() :
#             report.composerWindow().activateWindow()   
            report.composerWindow().show()
#                 report.composerWindow().setFocus(Qt.PopupFocusReason)

#                 report.composerWindow().setWindowFlags(report.composerWindow().windowFlags() | Qt.WindowStaysOnTopHint)

        pass
    
    def addReport(self, composerView):
        reportTitle = composerView.composerWindow().windowTitle()
        self.reportsList[reportTitle] = composerView
        self.comboReports.addItem(reportTitle)
        pass
    def addReportsList(self):
        for composerView in self.iface.activeComposers():
            reportTitle = composerView.composerWindow().windowTitle()
            self.reportsList[reportTitle] = composerView
            self.comboReports.addItem(reportTitle)
            composerView.composerWindow().hide()

    def openModeler(self):
        self.modelerDlg = ModelerDialog()
        self.modelerDlg.show()
        self.modelerDlg.btnSave.clicked.connect(self.addModel)
        self.modelerDlg.btnSaveAs.clicked.connect(self.addModel)
        self.modelerDlg.exec_()
        if self.modelerDlg.update:
            Processing.updateAlgsList()
            #self.toolbox.updateProvider('model')
        pass
        # run method that performs all the real work
    def addModel(self):
        if self.modelerDlg.update:
            modelName = self.modelerDlg.textName.text()
            if modelName in self.modelList:
                if self.modelList[modelName] != self.modelerDlg.alg.descriptionFile:
                    self.modelList[modelName + "1"] = self.modelerDlg.alg.descriptionFile
                    self.comboModels.addItem(modelName + "1")
            else:
                self.modelList[modelName] = self.modelerDlg.alg.descriptionFile
                self.comboModels.addItem(modelName)
        pass
    
    def runModel(self):
        if self.comboModels.count() < 2 or self.comboModels.currentIndex() < 1:
            return
        modelFileName = self.modelList[self.comboModels.currentText()]
        if modelFileName:
            try:
                alg = ModelerAlgorithm()
                alg.openModel(modelFileName)
                alg.descriptionFile = getTempFilename('model')
                text = alg.serialize()
                fout = open(alg.descriptionFile, 'w')
                fout.write(text)
                fout.close()
                alg.provider = Providers.providers['model']
                dlg = ParametersDialog(alg)
                dlg.exec_()

            except WrongModelException, e:
                QMessageBox.critical(self.iface.mainWindow(), self.tr('Could not open model'),
                        self.tr('The selected model could not be loaded.\n'
                                'Wrong line: %s') % e.msg)
    def loginNotify(self):
#         QMessageBox.critical(self.iface.mainWindow(), "login", "loginNotify")
        QObject.emit(self, SIGNAL("loginNotify"))
        
    def login(self):
        dlg = loginDialog(self.iface)
        dlg.show()
        result = dlg.exec_()

        if result == 1:
            self.setItemsEnabled(True)

        
    def initLists(self):
        self.modelList.clear()
        self.comboModels.clear()
        self.comboModels.addItem(" Run Health Models ")
        
        self.reportsList.clear()
        self.comboReports.clear()
        self.comboReports.addItem(" Health Reports ")
        
        self.addReportsList()
        self.addModelsList()
    
    def setItemsDisable(self):
        self.updateDataAction.setEnabled(False)
        self.createReportAction.setEnabled(False)
        self.comboReports.setEnabled(False)
        self.createModelAction.setEnabled(False)
        self.comboModels.setEnabled(False)