import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QFileDialog, QWidget, QProgressBar, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QRect
import cv2
import serial
from PIL import Image
from time import sleep

class ImageConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Converter")
        self.setGeometry(100, 100, 600, 400)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.browse_button = QPushButton("Browse Image", self)
        self.browse_button.clicked.connect(self.browse_image)

        self.rotate_button = QPushButton("Rotate Image", self)
        self.rotate_button.clicked.connect(self.image_rotate)

        self.default_button = QPushButton("Default", self)
        self.default_button.clicked.connect(self.default_image)

        self.clear_button = QPushButton("Clear Screen", self)
        self.clear_button.clicked.connect(self.clear_screen)

        self.convert_button = QPushButton("Convert and Send", self)
        self.convert_button.clicked.connect(self.convert_and_send)

        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(QRect(30, 430, 601, 20))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setDisabled(True)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.default_button)
        button_layout.addWidget(self.clear_button)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.rotate_button)
        layout.addLayout(button_layout)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.progressBar)


        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        self.file_name = None
        self.default_name = None

    def browse_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg);;All Files (*)", options=options)
        self.file_name = file_name
        self.default_name = file_name if file_name else self.default_name
        self.display()

    def tolcd_byte(self):
        image = cv2.imread(self.file_name)
        rescaled_image = cv2.resize(image, (128, 64))
        gray = cv2.cvtColor(rescaled_image, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        cv2.imwrite("abc.bmp", binary_image)
        image = Image.open("abc.bmp")
        lcd_image = image.convert('1')
        self.lcd_bytes = bytearray(lcd_image.tobytes())
        #print(self.lcd_bytes, len(self.lcd_bytes))

    def default_image(self):
        self.file_name = self.default_name
        self.display()
    def clear_screen(self):
        self.progressBar.setDisabled(False)
        try:
            self.progressBar.setValue(40)
            ser = serial.Serial('COM13', 9600, timeout=1)
            for char in "BB":    
                ser.write(char.encode())
            sleep(1)
            self.progressBar.setValue(80)
            ser.close()
            self.progressBar.setValue(100)
            print("Data sent successfully.")
        except serial.SerialException as e:
            print(f"Error: {e}")

    def image_rotate(self):
        rotated_image = cv2.rotate(cv2.imread(self.file_name), cv2.ROTATE_90_CLOCKWISE)
        self.file_name = self.default_name.replace(".png", "_r.png").replace(".jpg", "_r.jpg")
        cv2.imwrite(self.file_name, rotated_image)
        self.display()

    def display(self):
        if self.file_name:
            pixmap = QPixmap(self.file_name)
            scaled_pixmap = pixmap.scaledToWidth(400).scaledToHeight(400)
            self.image_label.setPixmap(scaled_pixmap)

    def send_lcd_bytes(self):
        self.progressBar.setDisabled(False)
        try:
            self.progressBar.setValue(40)
            ser = serial.Serial('COM13', 9600, timeout=1)
            for char in "AAAA":    
                ser.write(char.encode())
                print(ser.read(1))


            for byte in self.lcd_bytes:
                byte = byte.to_bytes(1, byteorder='big')
                ser.write(byte)
                confirmation = ser.read(1)
                while confirmation != b'\x61':
                    ser.write(byte)
                    confirmation = ser.read(1)

            ser.read(1)
            self.progressBar.setValue(80)
            ser.close()
            self.progressBar.setValue(100)
            print("Data sent successfully.")
        except serial.SerialException as e:
            print(f"Error: {e}")

    def convert_and_send(self):
        self.tolcd_byte()
        self.send_lcd_bytes()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageConverterApp()
    window.show()
    sys.exit(app.exec_())