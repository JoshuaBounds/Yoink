from typing import *
import os
import fnmatch
from PyQt5 import QtWidgets, QtCore
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

    def __init__(self, *args, **kwargs):
        super(Converter, self).__init__(*args, **kwargs)
        self.finished = Emitter()

    def run(self) -> None:
        for filename in fnmatch.filter(os.listdir(self.dir_path), self.src_txt):
            if os.path.isdir(os.path.join(self.dir_path, filename)):
                continue
            new_name = os.path.splitext(filename)[0] + self.dst_txt
            (
                ffmpeg
                .input(os.path.join(self.dir_path, filename))
                .output(os.path.join(self.dir_path, new_name))
                .run()
            )
        self.finished.signal.emit()


class YoinkMainPage(QtWidgets.QWidget):
    """
    Main page for YoinkWidget, contains downloader and converter.
    """

    def __init__(self, *args, **kwargs):
        super(YoinkMainPage, self).__init__(*args, **kwargs)

        self.downloader_started = Emitter()
        self.converter_started = Emitter()

        self.setLayout(QtWidgets.QVBoxLayout())

        # Downloader
        self.dir_browser = DirBrowserWidget()
        self.dir_browser.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.dir_browser)

        self.urls_txe = QtWidgets.QPlainTextEdit()
        self.layout().addWidget(self.urls_txe)

        download_btn = QtWidgets.QPushButton('download'.title())
        download_btn.clicked.connect(self.download)
        self.layout().addWidget(download_btn)

        self.downloader = Downloader()
        self.downloader.setAutoDelete(False)

        # Converter
        convert_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(convert_layout)

        self.convert_src_txf = QtWidgets.QLineEdit()
        convert_layout.addWidget(self.convert_src_txf)

        self.convert_dst_txf = QtWidgets.QLineEdit()
        convert_layout.addWidget(self.convert_dst_txf)

        convert_btn = QtWidgets.QPushButton('Convert')
        convert_btn.clicked.connect(self.convert)
        self.layout().addWidget(convert_btn)

        self.converter = Converter()
        self.converter.setAutoDelete(False)

    def download(self):
        """
        Performs the download task in a new thread.
        """
        self.downloader_started.signal.emit()
        self.downloader.urls = [x for x in self.urls_txe.toPlainText().split('\n') if x]
        self.downloader.dirpath = self.dir_browser.path
        QtCore.QThreadPool.globalInstance().start(self.downloader)

    def convert(self):
        """
        Performs the conversion task in a new thread.
        """
        self.converter_started.signal.emit()
        self.converter.dir_path = self.dir_browser.path
        self.converter.src_txt = self.convert_src_txf.text()
        self.converter.dst_txt = self.convert_dst_txf.text()
        QtCore.QThreadPool.globalInstance().start(self.converter)


class LoadingWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(LoadingWidget, self).__init__(*args, **kwargs)

        hlayout = QtWidgets.QHBoxLayout()
        self.setLayout(hlayout)

        vlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(vlayout)

        label = QtWidgets.QLabel('Loading...')
        label.setAlignment(QtCore.Qt.AlignCenter)
        hlayout.addWidget(label)


class YoinkWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self.setLayout(QtWidgets.QStackedLayout())

        main_page = YoinkMainPage()
        main_page.downloader.finished.signal.connect(self.switch_main_page)
        main_page.converter.finished.signal.connect(self.switch_main_page)
        main_page.downloader_started.signal.connect(self.switch_loading_page)
        main_page.converter_started.signal.connect(self.switch_loading_page)
        self.layout().addWidget(main_page)

        loading_page = LoadingWidget()
        self.layout().addWidget(loading_page)

    def switch_main_page(self):
        self.layout().setCurrentIndex(0)

    def switch_loading_page(self):
        self.layout().setCurrentIndex(1)


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = YoinkWidget()
    win.setStyleSheet('''
        * {
            background-color: rgb(40, 40, 40);
            color: rgb(0, 255, 255);
            font-family: Arial;
            font-size: 10pt;
            font-weight: 200;
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
    ''')
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
