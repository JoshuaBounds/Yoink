"""
TODO:
    Check all typing.
    Redo window state preservation.
"""

import os
import shutil
import json
import warnings
from tempfile import TemporaryDirectory
from typing import *
import youtube_dl
import ffmpy3
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class YoinkRunnable(QRunnable):
    """
    Performs the task of downloading video using the given data.
    """

    urls: List[AnyStr] = None
    output_ext: AnyStr = None
    output_dir: AnyStr = None
    finished: 'Emitter' = None

    class Emitter(QObject):
        signal: pyqtSignal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(YoinkRunnable, self).__init__(*args, **kwargs)
        self.finished = self.Emitter()

    @staticmethod
    def convert_dir(src_dir, dst_dir, file_ext):
        """
        Converts all files in the given directory (src_dir) with the
        output going to the given directory (dst_dir).
        :param src_dir:
            Source directory path.
        :param dst_dir:
            Destination directory path.
        :param file_ext:
            File type to convert all files to.
        """
        for file_name in os.listdir(src_dir):
            file_path = os.path.join(src_dir, file_name)
            new_file_path = os.path.join(
                dst_dir,
                os.path.splitext(file_name)[0] + '.' + file_ext
            )
            converter = ffmpy3.FFmpeg(
                inputs={file_path: None},
                outputs={new_file_path: None}
            )
            converter.run()

    @staticmethod
    def copy_dir(src_dir, dst_dir):
        """
        Copies all files in a given directory (src_dir) to the given
        directory (dst_dir).
        :param src_dir:
            Source directory path.
        :param dst_dir:
            Destination directory path.
        """
        for file_name in os.listdir(src_dir):
            shutil.copyfile(
                os.path.join(src_dir, file_name),
                os.path.join(dst_dir, file_name)
            )

    @staticmethod
    def download_urls(urls, dst_dir):
        """
        Downloads given urls to the given directory.
        :param urls:
            youtube urls to download.
        :param dst_dir:
            Destination directory for downloaded files.
        """
        out_template = {'outtmpl': os.path.join(dst_dir, '%(title)s.%(ext)s')}
        with youtube_dl.YoutubeDL(out_template) as downloader:
            try:
                downloader.download(urls)
            except youtube_dl.DownloadError as e:
                warnings.warn('download failure')
                warnings.warn(e)

    def run(self):

        print('>> urls:', self.urls)
        print('>> output_ext:', self.output_ext)
        print('>> output_dir:', self.output_dir)

        with TemporaryDirectory() as temp_dir:
            self.download_urls(self.urls, temp_dir)
            if self.output_ext is None:
                self.copy_dir(temp_dir, self.output_dir)
            else:
                self.convert_dir(temp_dir, self.output_dir, self.output_ext)

        self.finished.signal.emit()


class BrowserWidget(QWidget):
    """
    Creates a directory browser widget that displays the currently
    selected directory location.
    """

    path_label: QLabel = None
    browser_starting_dir: AnyStr = None

    def __init__(self, *args, **kwargs):
        super(BrowserWidget, self).__init__(*args, **kwargs)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.path_label = path_label = QLabel(self)
        main_layout.addWidget(path_label)

        browser_button = QPushButton('Browse', self)
        browser_button.clicked.connect(self.open_dir_browser)
        browser_button.setMaximumWidth(80)
        main_layout.addWidget(browser_button)

    def open_dir_browser(self) -> AnyStr:
        """
        Opens a file browser to set the widgets displayed directory.
        :return:
            Displayed file path.
        """
        path = QFileDialog.getExistingDirectory(
            self,
            'set output directory'.title(),
            self.browser_starting_dir or os.environ['userprofile'],
            QFileDialog.ShowDirsOnly
        )
        if path:
            self.path_label.setText(path)
            self.browser_starting_dir = path
        return self.path_label.text()


class DownloadWidget(QWidget):
    """
    Creates a simple dir path display and browser combo.
    """

    url_field: QPlainTextEdit = None
    browser_widget: BrowserWidget = None
    download_button: QPushButton = None

    def __init__(self, *args, **kwargs):
        super(DownloadWidget, self).__init__(*args, **kwargs)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        form_layout = QFormLayout(self)
        main_layout.addLayout(form_layout)

        self.url_field = url_field = QPlainTextEdit(self)
        form_layout.addRow('download urls:'.title(), url_field)

        self.ext_combobox = ext_combobox = QComboBox(self)
        ext_combobox.addItem('default'.title())
        ext_combobox.addItems(sorted(('avi', 'mkv', 'mp3', 'mp4', 'wav')))
        form_layout.addRow('output file type:'.title(), ext_combobox)

        self.browser_widget = browser_widget = BrowserWidget(self)
        form_layout.addRow('output directory:'.title(), browser_widget)

        self.download_button = download_button = (
            QPushButton('download'.title(), self)
        )
        download_button.setObjectName('download_button')
        main_layout.addWidget(download_button)

    def get_download_urls(self):
        """
        :return:
            All urls in the url field
        """
        return [
            x for x in self.url_field.toPlainText().split('\n')
            if x
        ]

    def get_output_ext(self):
        """
        :return:
            The current selected output extension.
            Returns `None` instead of `default`.
        """
        extension = self.ext_combobox.currentText()
        return (
            None
            if extension.casefold() == 'default'.casefold() else
            extension
        )

    def get_output_dir(self):
        """
        :return:
            The path currently in the output dir field.
            Returns the `userprofile` env var, if path is invalid.
        """
        path = self.browser_widget.path_label.text()
        return path if os.path.exists(path) else os.environ['userprofile']


class LoadingWidget(QWidget):
    """
    Displayed when `YoinkWidget` requires the user to wait while the
    previous action is being processed.
    """

    def __init__(self, *args, **kwargs):
        super(LoadingWidget, self).__init__(*args, **kwargs)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        loading_label = QLabel('loading', self)
        loading_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(loading_label)


class YoinkWidget(QWidget):
    """
    Yoink's main widget.
    """

    _main_layout: QStackedLayout = None
    _runnable: YoinkRunnable = None

    download_widget: DownloadWidget = None
    loading_widget: LoadingWidget = None

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')
        self.resize(600, 400)
        self.setStyleSheet('''
            * {
                background-color: rgb(40, 40, 40);
                color: rgb(0, 255, 255);
                font-family: Arial;
                font-size: 10pt;
                font-weight: 200;
            }
            QComboBox {
                background-color: rgb(0, 55, 55);
                padding: 5px;
                border: 2px solid rgb(0, 255, 255);
                border-radius: 3px
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
            QPushButton#download_button {
                font-size: 12pt;
            }
        ''')
        self._main_layout = main_layout = QStackedLayout(self)
        self.setLayout(main_layout)

        self.download_widget = download_widget = DownloadWidget(self)
        download_widget.download_button.clicked.connect(self.download)
        main_layout.addWidget(download_widget)

        self.loading_widget = loading_widget = LoadingWidget(self)
        main_layout.addWidget(loading_widget)

        self._runnable = runnable = YoinkRunnable()
        runnable.setAutoDelete(False)
        runnable.finished.signal.connect(
            lambda: main_layout.setCurrentIndex(0)
        )

    def download(self):
        """
        Starts downloading process using data gathered from the gui.
        """
        runnable = self._runnable
        runnable.urls = self.download_widget.get_download_urls()
        runnable.output_ext = self.download_widget.get_output_ext()
        runnable.output_dir = self.download_widget.get_output_dir()

        self._main_layout.setCurrentIndex(1)
        QThreadPool.globalInstance().start(runnable)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.show()

    sys.exit(app.exec_())
