from typing import *
import subprocess
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

        self.starting_dir = starting_dir or os.path.expanduser('~')

        self.h_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.h_layout)

        self.path_txf = QtWidgets.QLabel(self.starting_dir)
        self.h_layout.addWidget(self.path_txf)

        self.browser_btn = QtWidgets.QPushButton('browse'.title())
        self.browser_btn.setMaximumWidth(80)
        self.browser_btn.clicked.connect(self.open_dir_browser)
        self.h_layout.addWidget(self.browser_btn)

        self.explorer_btn = QtWidgets.QPushButton('open folder'.title())
        self.explorer_btn.setMaximumWidth(110)
        self.explorer_btn.clicked.connect(self.open_explorer)
        self.h_layout.addWidget(self.explorer_btn)

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
            path = os.path.abspath(path)
            self.path_txf.setText(path)
            self.starting_dir = path
        return self.path_txf.text()

    def open_explorer(self):
        subprocess.Popen(r'explorer "%s"' % self.path)


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

        v_layout = QtWidgets.QVBoxLayout()
        self.setLayout(v_layout)

        # Browser widget

        self.dir_browser_widget = DirBrowserWidget()
        v_layout.addWidget(self.dir_browser_widget)

        # Tabs widget

        self.tabs_widget = QtWidgets.QTabWidget()
        v_layout.addWidget(self.tabs_widget)

        self.downloader_widget = QtWidgets.QWidget()
        self.tabs_widget.addTab(self.downloader_widget, "Downloader")

        self.converter_widget = QtWidgets.QWidget()
        self.tabs_widget.addTab(self.converter_widget, "Converter")

        # Downloader Tab

        self.downloader_layout = QtWidgets.QVBoxLayout()
        self.downloader_widget.setLayout(self.downloader_layout)

        self.download_urls = QtWidgets.QPlainTextEdit("https://youtu.be/dQw4w9WgXcQ?si=ymodleyJzawYilQW")
        self.downloader_layout.addWidget(self.download_urls)

        self.download_button = QtWidgets.QPushButton("Download")
        self.download_button.clicked.connect(self.download)
        self.downloader_layout.addWidget(self.download_button)

        # Converter Tab

        self.converter_layout = QtWidgets.QVBoxLayout()
        self.converter_widget.setLayout(self.converter_layout)

        self.src_extension_txf = QtWidgets.QLineEdit(".wav")
        self.converter_layout.addWidget(self.src_extension_txf)

        self.dst_extension_txf = QtWidgets.QLineEdit(".mp3")
        self.converter_layout.addWidget(self.dst_extension_txf)

        self.convert_button = QtWidgets.QPushButton("Convert")
        self.convert_button.clicked.connect(self.convert)
        self.converter_layout.addWidget(self.convert_button)

        self.remove_converted_checkbox = QtWidgets.QCheckBox("Remove Converted")
        self.converter_layout.addWidget(self.remove_converted_checkbox)

        self.converter_layout.addStretch()

    def download(self):
        """
        Performs the download task in a new thread.
        """
        self.downloader_started.signal.emit()
        self.downloader.urls = [x for x in self.download_urls.toPlainText().split('\n') if x]
        self.downloader.dirpath = self.dir_browser_widget.path
        QtCore.QThreadPool.globalInstance().start(self.downloader)

    def convert(self):
        """
        Performs the conversion task in a new thread.
        """
        self.converter_started.signal.emit()
        self.converter.dir_path = self.dir_browser_widget.path
        self.converter.src_txt = "*" + self.src_extension_txf.text()
        self.converter.dst_txt = self.dst_extension_txf.text()
        self.converter.remove_converted = self.remove_converted_checkbox.isChecked()
        QtCore.QThreadPool.globalInstance().start(self.converter)


class LoadingWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(LoadingWidget, self).__init__(*args, **kwargs)

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

        self.tabs_widget = YoinkTabsWidget()
        self.tabs_widget.downloader.finished.signal.connect(self.switch_main_page)
        self.tabs_widget.downloader_started.signal.connect(self.switch_loading_page)
        self.tabs_widget.converter.finished.signal.connect(self.switch_main_page)
        self.tabs_widget.converter_started.signal.connect(self.switch_loading_page)
        self.layout().addWidget(self.tabs_widget)

        loading_widget = LoadingWidget()
        self.layout().addWidget(loading_widget)

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
