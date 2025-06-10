import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO

LABEL_DIR = r"\\192.168.1.183:3000\LABEL"  # <-- CHANGE this to the real path (can be a mapped drive or network share)
LABEL_FILENAME = "barcodejob.txt"      # The filename to use, can be anything (check your workflow)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mainwindow.ui", self)  # Load the Qt Designer UI

        self.statusLabel = self.findChild(QtWidgets.QLabel, "statusLabel")
        self.statusIndicator = self.findChild(QtWidgets.QLabel, "statusIndicator")
        self.numberEdit = self.findChild(QtWidgets.QLineEdit, "numberEdit")
        self.barcodeLabel = self.findChild(QtWidgets.QLabel, "barcodeLabel")
        self.sendButton = self.findChild(QtWidgets.QPushButton, "sendButton")

        self.sendButton.clicked.connect(self.send_to_label_dir)
        self.numberEdit.textChanged.connect(self.update_barcode)

        self.statusLabel.setText("Ready")
        self.statusIndicator.setStyleSheet("background-color: orange; border-radius: 10px;")

        self.update_barcode()

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
            code128 = barcode.get('code128', text, writer=ImageWriter())
            fp = BytesIO()
            code128.write(fp, {
                "module_height": 40.0,
                "module_width": 0.8,
                "font_size": 18,
                "text_distance": 4.0,
                "quiet_zone": 6.0,
                "dpi": 150
            })
            fp.seek(0)
            image = Image.open(fp).convert("RGB")
            image = image.resize((400, 100), Image.LANCZOS)

            data = image.tobytes("raw", "RGB")
            qimage = QtGui.QImage(data, image.size[0], image.size[1], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(qimage)

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

    def send_to_label_dir(self):
        data = self.numberEdit.text()
        if not data.isdigit():
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter numbers only.")
            return
        try:
            if not os.path.exists(LABEL_DIR):
                QtWidgets.QMessageBox.critical(self, "Error", f"LABEL directory does not exist:\n{LABEL_DIR}")
                return
            filepath = os.path.join(LABEL_DIR, LABEL_FILENAME)
            with open(filepath, "w") as f:
                f.write(data)
            QtWidgets.QMessageBox.information(self, "Sent", f"Barcode data written to LABEL:\n{filepath}")
            self.statusLabel.setText("Written")
            self.statusIndicator.setStyleSheet("background-color: green; border-radius: 10px;")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to write: {e}")
            self.statusLabel.setText("Failed")
            self.statusIndicator.setStyleSheet("background-color: red; border-radius: 10px;")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
