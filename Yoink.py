
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class YoutubeDLWidget(QStackedWidget):

    def __init__(self):
        super(YoutubeDLWidget, self).__init__()

        # Creates the controls widget.

        controls_widget = QWidget(self)
        controls_layout = QFormLayout(controls_widget)

        controls_url_bar = QLineEdit(controls_widget)
        controls_layout.addRow('Download URL', controls_url_bar)

        controls_widget.setLayout(controls_layout)
        self.addWidget(controls_widget)

        # Creates the loading widget.

        loading_widget = QWidget(self)
        loading_layout = QVBoxLayout(self)

        loading_label = QLabel('loading', self)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)

        loading_widget.setLayout(loading_layout)
        self.addWidget(loading_widget)


class FFMPEGWidget(QWidget):
    pass


class DirectoryWidget(QWidget):
    pass


class Yoink(QWidget):
    pass


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    ytdl = YoutubeDLWidget()
    ytdl.show()

    app.exec_()
