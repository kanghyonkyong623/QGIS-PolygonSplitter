
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

from qgis.core import *
from qgis.gui import *
import json

from dialogs import *

from ui_loginDialog import Ui_Dialog

#global variable with short to full algorithm names

class loginDialog(QDialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.iface = iface
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect( self.login )
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.finished)
        self.reply = None
        self.request_qt = None
        self.setModal(True)
        self.address = "http://95.85.19.14:3000/api/v1/sessions"
        self.setCursor(Qt.ArrowCursor)
        
    def login(self):
        userName = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        self.address = self.ui.lineEdit_url.text()
        data = "{\"user\":{\"email\":\"%s\",\"password\":\"%s\"}}" % (userName, password)

        url = QUrl(self.address)
        self.request_qt = QNetworkRequest(url)
        self.request_qt.setRawHeader("Content-Type", "application/json")
        self.request_qt.setRawHeader("Accept", "application/json")
        self.request_qt.setRawHeader("Content-Length", QByteArray.number(len(data)))
        
        #QMessageBox.warning(self, "userName", data)
        self.reply = self.manager.post(self.request_qt, data)
        self.ui.pushButton.setEnabled(False)
#         QMessageBox.warning(self, "userName", 
#                             str(self.urlencode_post({"user":self.urlencode_post(data)})))
        
    def construct_multipart(self, data, files):
        multiPart = QHttpMultiPart(QHttpMultiPart.FormDataType)
        for key, value in data.items():
          textPart = QHttpPart()
          textPart.setHeader(QNetworkRequest.ContentDispositionHeader,
            "form-data; name=\"%s\"" % key)
          textPart.setBody(value)
          multiPart.append(textPart)
        
        for key, file in files.items():
          imagePart = QHttpPart()
          #imagePart.setHeader(QNetworkRequest::ContentTypeHeader, ...);
          fileName = QFileInfo(file.fileName()).fileName()
          imagePart.setHeader(QNetworkRequest.ContentDispositionHeader,
            "form-data; name=\"%s\"; filename=\"%s\"" % (key, fileName))
          imagePart.setBodyDevice(file);
          multiPart.append(imagePart)
        return multiPart
    
    def urlencode_post(self, data):
        post_params = QUrl()
        for (key, value) in data.items():
            post_params.addQueryItem(key, unicode(value))            

        return post_params.encodedQuery()
    
    def finished(self):
        resultString = str(self.reply.readAll())
        #QMessageBox.warning(self, "userName", resultString[1:15])
        self.ui.pushButton.setEnabled(True)
        
        if resultString[1:15] == "\"success\":true":
            self.accept()
        else:
            QMessageBox.warning(self, "Wrong", "Invalid Username or Password")