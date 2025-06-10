import sys
import socket
from PyQt5 import QtWidgets, QtGui, QtCore, uic
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO

PRINTER_IP = "192.168.1.183"  # or "192.168.1.183"
PRINTER_PORT = 3000        # or your printer's port

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mainwindow.ui", self)  # Load the Qt Designer UI

        # Get widgets by their objectName (from .ui)
        self.statusLabel = self.findChild(QtWidgets.QLabel, "statusLabel")
        self.statusIndicator = self.findChild(QtWidgets.QLabel, "statusIndicator")
        self.numberEdit = self.findChild(QtWidgets.QLineEdit, "numberEdit")
        self.barcodeLabel = self.findChild(QtWidgets.QLabel, "barcodeLabel")
        self.sendButton = self.findChild(QtWidgets.QPushButton, "sendButton")

        self.sendButton.clicked.connect(self.send_to_printer)
        self.numberEdit.textChanged.connect(self.update_barcode)

        # Timer for auto-connection check
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(3000)  # check every 3 seconds
        self.check_connection()

        self.update_barcode()  # draw barcode for empty/initial value

    def set_status(self, connected):
        if connected:
            self.statusLabel.setText("Connected")
            self.statusIndicator.setStyleSheet("background-color: green; border-radius: 10px;")
            self.sendButton.setEnabled(True)
        else:
            self.statusLabel.setText("Not Connected")
            self.statusIndicator.setStyleSheet("background-color: red; border-radius: 10px;")
            self.sendButton.setEnabled(False)

    def check_connection(self):
        try:
            with socket.create_connection((PRINTER_IP, PRINTER_PORT), timeout=1):
                self.set_status(True)
        except Exception:
            self.set_status(False)

    def update_barcode(self):
        text = self.numberEdit.text()
        if not text.isdigit():
            self.barcodeLabel.setText("Enter numbers only.")
            self.barcodeLabel.setPixmap(QtGui.QPixmap())
            return
        if not text:
            self.barcodeLabel.setText("Barcode will appear here")
            self.barcodeLabel.setPixmap(QtGui.QPixmap())
            return
        try:
            # Generate barcode at a fixed, classic size (wide, not tall)
            code128 = barcode.get('code128', text, writer=ImageWriter())
            fp = BytesIO()
            code128.write(fp, {
                "module_height": 40.0,    # classic barcode height
                "module_width": 0.8,      # wider bars
                "font_size": 18,
                "text_distance": 4.0,
                "quiet_zone": 6.0,
                "dpi": 150
            })
            fp.seek(0)
            image = Image.open(fp).convert("RGB")
            image = image.resize((400, 100), Image.LANCZOS)  # classic barcode aspect ratio

            # Convert to QPixmap
            data = image.tobytes("raw", "RGB")
            qimage = QtGui.QImage(data, image.size[0], image.size[1], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(qimage)

            # If the label is smaller, scale down with aspect ratio
            label_w = self.barcodeLabel.width()
            label_h = self.barcodeLabel.height()
            if label_w < 400 or label_h < 100:
                pixmap = pixmap.scaled(label_w, label_h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

            self.barcodeLabel.setPixmap(pixmap)
            self.barcodeLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.barcodeLabel.setText("")
        except Exception as e:
            self.barcodeLabel.setText("Barcode error.")
            self.barcodeLabel.setPixmap(QtGui.QPixmap())

    def resizeEvent(self, event):
        self.update_barcode()
        super().resizeEvent(event)

    def send_to_printer(self):
        data = self.numberEdit.text()
        if not data.isdigit():
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter numbers only.")
            return
        try:
            with socket.create_connection((PRINTER_IP, PRINTER_PORT), timeout=3) as s:
                s.sendall((data + "\n").encode("utf-8"))
            QtWidgets.QMessageBox.information(self, "Sent", "Barcode data sent to printer.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to send: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
