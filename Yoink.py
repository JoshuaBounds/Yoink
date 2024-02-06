from typing import *
import os
import fnmatch
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
import ffmpeg
import yt_dlp


class DirBrowserWidget(QtWidgets.QWidget):
    """
    Displays the current path, and a button to open a dir browser to set
    the current path.
    """

    def __init__(self, *args, starting_dir=None, **kwargs):
        """
        :param starting_dir:
            Init the widget with this path as default.
            If not given, is set to cwd.
        """
        super(DirBrowserWidget, self).__init__(*args, **kwargs)

        self.starting_dir = starting_dir or os.getcwd()

        self.setLayout(QtWidgets.QHBoxLayout())

        self.path_txf = QtWidgets.QLabel(self.starting_dir)
        self.layout().addWidget(self.path_txf)

        browser_btn = QtWidgets.QPushButton('browse'.title())
        browser_btn.setMaximumWidth(80)
        browser_btn.clicked.connect(self.open_dir_browser)
        self.layout().addWidget(browser_btn)

    @property
    def path(self):
        return self.path_txf.text()

    def open_dir_browser(self):
        """
        Opens a dir browser to set the widgets displayed directory.
        :return:
            Selected dir path.
        """
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'set output directory'.title(),
            self.starting_dir,
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if path:
            self.path_txf.setText(path)
            self.starting_dir = path
        return self.path_txf.text()


class Emitter(QtCore.QObject):
    """
    Allows signals to be emitted from objects that do not
    inherit from QObject.
    """
    signal = QtCore.pyqtSignal()


class Downloader(QtCore.QRunnable):
    """
    Downloads media.
    """

    urls: List = None
    dirpath: AnyStr = None

    def __init__(self, *args, **kwargs):
        super(Downloader, self).__init__(*args, **kwargs)
        self.finished = Emitter()

    def run(self) -> None:
        opts = {'outtmpl': os.path.join(self.dirpath, '%(title)s.%(ext)s')}
        with yt_dlp.YoutubeDL(opts) as downloader:
            downloader.download(self.urls)
        self.finished.signal.emit()


class Converter(QtCore.QRunnable):
    """
    Converts media.
    """

    dir_path: AnyStr = None
    src_txt: AnyStr = None
    dst_txt: AnyStr = None
    remove_converted = False

    def __init__(self, *args, **kwargs):
        super(Converter, self).__init__(*args, **kwargs)
        self.finished = Emitter()

    def run(self) -> None:
        for filename in fnmatch.filter(os.listdir(self.dir_path), self.src_txt):
            if os.path.isdir(os.path.join(self.dir_path, filename)):
                continue
            new_name = os.path.splitext(filename)[0] + self.dst_txt
            src_path = os.path.join(self.dir_path, filename)
            (
                ffmpeg
                .input(src_path)
                .output(os.path.join(self.dir_path, new_name))
                .run()
            )
            if self.remove_converted:
                os.remove(src_path)
        self.finished.signal.emit()


class YoinkTabsWidget(QtWidgets.QWidget):
    """
    Widget containing the main control tabs for yoink controls
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.downloader_started = Emitter()
        self.converter_started = Emitter()

        self.downloader = Downloader()
        self.downloader.setAutoDelete(False)

        self.converter = Converter()
        self.converter.setAutoDelete(False)

        # Main layout

        self.setLayout(QtWidgets.QVBoxLayout())

        # Browser widget

        self.dirBrowserWidget = DirBrowserWidget()
        self.layout().addWidget(self.dirBrowserWidget)

        # Tabs widget

        self.tabsWidget = QtWidgets.QTabWidget()
        self.layout().addWidget(self.tabsWidget)

        self.downloaderWidget = QtWidgets.QWidget()
        self.tabsWidget.addTab(self.downloaderWidget, "Downloader")

        self.converterWidget = QtWidgets.QWidget()
        self.tabsWidget.addTab(self.converterWidget, "Converter")

        # Downloader Tab

        self.downloaderWidget.setLayout(QtWidgets.QVBoxLayout())

        self.downloadURLs = QtWidgets.QPlainTextEdit("https://youtu.be/dQw4w9WgXcQ?si=ymodleyJzawYilQW")
        self.downloaderWidget.layout().addWidget(self.downloadURLs)

        self.downloadButton = QtWidgets.QPushButton("Download")
        self.downloadButton.clicked.connect(self.download)
        self.downloaderWidget.layout().addWidget(self.downloadButton)

        # Converter Tab

        self.converterWidget.setLayout(QtWidgets.QVBoxLayout())

        self.srcExtension = QtWidgets.QLineEdit(".wav")
        self.converterWidget.layout().addWidget(self.srcExtension)

        self.dstExtension = QtWidgets.QLineEdit(".mp3")
        self.converterWidget.layout().addWidget(self.dstExtension)

        self.convertButton = QtWidgets.QPushButton("Convert")
        self.convertButton.clicked.connect(self.convert)
        self.converterWidget.layout().addWidget(self.convertButton)

        self.removeConvertedCheckbox = QtWidgets.QCheckBox("Remove Converted")
        self.converterWidget.layout().addWidget(self.removeConvertedCheckbox)

        self.converterWidget.layout().addStretch()

    def download(self):
        """
        Performs the download task in a new thread.
        """
        self.downloader_started.signal.emit()
        self.downloader.urls = [x for x in self.downloadURLs.toPlainText().split('\n') if x]
        self.downloader.dirpath = self.dirBrowserWidget.path
        QtCore.QThreadPool.globalInstance().start(self.downloader)

    def convert(self):
        """
        Performs the conversion task in a new thread.
        """
        self.converter_started.signal.emit()
        self.converter.dir_path = self.dirBrowserWidget.path
        self.converter.src_txt = "*" + self.srcExtension.text()
        self.converter.dst_txt = self.dstExtension.text()
        self.converter.remove_converted = self.removeConvertedCheckbox.isChecked()
        QtCore.QThreadPool.globalInstance().start(self.converter)


class LoadingPage(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(LoadingPage, self).__init__(*args, **kwargs)

        h_layout = QtWidgets.QHBoxLayout()
        self.setLayout(h_layout)

        v_layout = QtWidgets.QVBoxLayout()
        h_layout.addLayout(v_layout)

        label = QtWidgets.QLabel('Loading...')
        label.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(label)


class YoinkWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self.setLayout(QtWidgets.QStackedLayout())

        self.tabsWidget = YoinkTabsWidget()
        self.tabsWidget.downloader.finished.signal.connect(self.switch_main_page)
        self.tabsWidget.downloader_started.signal.connect(self.switch_loading_page)
        self.tabsWidget.converter.finished.signal.connect(self.switch_main_page)
        self.tabsWidget.converter_started.signal.connect(self.switch_loading_page)
        self.layout().addWidget(self.tabsWidget)

        loading_page = LoadingPage()
        self.layout().addWidget(loading_page)

    def switch_main_page(self):
        self.layout().setCurrentIndex(0)

    def switch_loading_page(self):
        self.layout().setCurrentIndex(1)


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = YoinkWidget()
    win.setWindowTitle('Yoink')
    win.resize(600, 400)
    win.setStyleSheet('''
        * {
            background-color: rgb(40, 40, 40);
            color: rgb(0, 255, 255);
            font-family: Arial;
            font-size: 10pt;
            font-weight: 200;
        }
        QLabel#sectionLabel {
            background-color: rgb(0, 55, 55);
        }
        QPlainTextEdit {
            font-family: Fixedsys;
            background-color: black;
        }
        QPushButton {
            background-color: rgb(0, 55, 55);
            padding: 5px;
            border: 2px solid rgb(0, 255, 255);
            border-radius: 3px
        }
        QPushButton:hover {
            background-color: rgb(0, 255, 255);
            color: black;
        }
        QCheckBox::indicator {
            background-color: rgb(0, 55, 55);
            padding: 5px;
            border: 2px solid rgb(0, 255, 255);
            border-radius: 3px
        }
        QCheckBox::indicator:checked {
            background-color: rgb(0, 255, 255);
        }
        QCheckBox::indicator:unchecked {
            background-color: rgb(0, 55, 55);
        }
        QTabBar::tab {
            background-color: rgb(40, 40, 40);
        }
        QTabBar::tab:selected {
            background-color: rgb(0, 55, 55);
            padding: 5px;
            border: 2px solid rgb(0, 255, 255);
            border-radius: 3px
        }
    ''')
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
