from PySide6 import QtCore, QtWidgets
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl, Slot, QObject, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtCore import QJsonDocument, QJsonParseError
from PySide6.QtCore import QUrl, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtCore import QJsonDocument, QJsonParseError


class ReplyHandler(QtCore.QObject):
    finished = Signal(object)

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.buffer = b""

    @Slot()
    def handle_ready_read(self):
        reply = self.sender()
        self.buffer += reply.readAll()

    @Slot()
    def handle_finished(self):
        print("handle finished")
        reply = self.sender()
        if reply.error() != QNetworkReply.NoError:
            print("Request failed:", reply.errorString())
        json_doc = QJsonDocument.fromJson(self.buffer)
        if json_doc.isNull():
            print("Failed to parse JSON")
        else:
            print("Passing JSON to callback")
            self.callback(json_doc.toVariant())
        reply.deleteLater()


class APIClient:
    def __init__(self):
        self.base_url = "https://ilaris-online.de/api/"
        self.manager = QNetworkAccessManager()
        self.handlers = []
        print("api client created")

    def request(self, path, callback):
        print("request running")
        url = QUrl(self.base_url + path)
        request = QNetworkRequest(url)
        reply = self.manager.get(request)
        handler = ReplyHandler(callback)
        reply.readyRead.connect(handler.handle_ready_read)
        reply.finished.connect(handler.handle_finished)
        self.handlers.append(handler)  # prevent from beeing collected       
        
        loop = QtCore.QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()




if __name__ == "__main__":
    # call directly for debugging
    def on_response(data):
        print("got data")
        print([d.get("name") for d in data])

    app = QtWidgets.QApplication([])
    api = APIClient()
    api.request("ilaris/kreatur/", print)

    app.exec()