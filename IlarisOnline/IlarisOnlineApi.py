from PySide6 import QtCore, QtWidgets
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl, Slot, QObject, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtCore import QJsonDocument, QJsonParseError
from PySide6.QtCore import QUrl, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtCore import QJsonDocument, QJsonParseError
from Wolke import Wolke

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
        error = False
        status_code = 200
        if reply.error() != QNetworkReply.NoError:
            error = reply.errorString()
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            print("Request failed:", status_code, reply.errorString())
        json_doc = QJsonDocument.fromJson(self.buffer)
        if json_doc.isNull():
            data = {"details": "Failed to parse JSON"}
        else:
            data = json_doc.toVariant()
        self.callback(data, error=error, status=status_code)
        try:
            reply.deleteLater()
        except RuntimeError:
            pass


class APIClient:
    def __init__(self, token=None):
        print("init client")
        self.base_url = Wolke.Settings.get("IO_APIUrl", "")
        print(self.base_url)
        if not self.base_url:
            print("No API URL set, using default")
            self.base_url = "https://ilaris-online.de/api/"
        if not self.base_url.endswith("/"):
            self.base_url += "/"
        self.manager = QNetworkAccessManager()
        self.handlers = []
        self.token = Wolke.Settings.get("IO_APIToken", "")
        if token is not None:
            self.token = token
        print("is api created?")

    def request(self, path, callback, method="GET", payload=None):
        print("request running")
        url = QUrl(self.base_url + path)
        request = QNetworkRequest(url)
        if self.token:
            print("token added to request")
            request.setRawHeader(b"Authorization", b"Token " + self.token.encode())
        if method == "POST":
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            reply = self.manager.post(request, QJsonDocument(payload).toJson())
        elif method == "PUT":
            request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
            reply = self.manager.put(request, QJsonDocument(payload).toJson())
        else:
            reply = self.manager.get(request)
        handler = ReplyHandler(callback)
        reply.readyRead.connect(handler.handle_ready_read)
        reply.finished.connect(handler.handle_finished)
        self.handlers.append(handler)  # prevent from beeing collected       
        
        loop = QtCore.QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()
    
    def get(self, path, callback):
        self.request(path, callback, "GET")
    
    def post(self, path, payload, callback):
        self.request(path, callback, method="POST", payload=payload)

    def update(self, path, payload, callback):
        self.request(path, callback, method="PUT", payload=payload)

    def login(self, username, password, callback):
        print("LOGIN CALLED")
        url = self.base_url[:-4] + "/accounts/token"
        print(url)
        # url = "http://localhost:8000/accounts/token"
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        data = {
            "username": username,
            "password": password,
        }
        handler = ReplyHandler(callback)
        reply = self.manager.post(request, QJsonDocument(data).toJson())
        reply.readyRead.connect(handler.handle_ready_read)
        reply.finished.connect(handler.handle_finished)
        self.handlers.append(handler)        
        loop = QtCore.QEventLoop()
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