"""
TODO:
    Redo window state preservation.
"""

from typing import *
import warnings
import shutil
import os
import subprocess
from tempfile import TemporaryDirectory
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


FFMPEG = 'ffmpeg.exe'
YTDL = 'yt-dlp.exe'


class Emitter(QObject):
    signal: pyqtSignal = pyqtSignal()


class YoinkRunnable(QRunnable):
    """
    Performs the task of downloading and/or converting the video
    with completed files being written to the given dir.
    """

    urls: List[AnyStr] = None
    output_ext: AnyStr = None
    output_dir: AnyStr = None

    finished: Emitter = None

    def __init__(self, *args, **kwargs):
        """
        :param urls:
            urls to download
        :param output_ext:
            if provided, converts downloaded videos to this type
        :param output_dir:
            output dir for completed files
        """
        super(YoinkRunnable, self).__init__(*args, **kwargs)
        self.finished = Emitter()

    @staticmethod
    def convert_dir(src_dir: AnyStr, dst_dir: AnyStr, file_ext: AnyStr):
        """
        Converts all files in the given directory (src_dir) with the
        output going to the given directory (dst_dir).
        :param src_dir:
            Source directory path.
        :param dst_dir:
            Destination directory path.
        :param file_ext:
            File type to convert all files to (should not include the `.`).
        """
        for file_name in os.listdir(src_dir):
            file_path = os.path.join(src_dir, file_name)
            new_file_path = os.path.join(
                dst_dir,
                os.path.splitext(file_name)[0] + '.' + file_ext
            )
            proc = subprocess.Popen(f'{FFMPEG} -i {file_path} {new_file_path}')
            proc.wait()

    @staticmethod
    def copy_dir(src_dir: AnyStr, dst_dir: AnyStr):
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
                os.path.join(dst_dir, file_name),
            )

    @staticmethod
    def download_urls(
            urls: List[AnyStr],
            dst_dir: AnyStr,
            out_template: AnyStr = '%(title)s.%(ext)s'):
        """
        Downloads given urls to the given directory.
        :param urls:
            urls to download.
        :param dst_dir:
            Destination directory for downloaded files.
        :param out_template:
            yt-dlp output template.
        """
        for url in urls:
            new_out_template = os.path.join(dst_dir, out_template)
            proc = subprocess.Popen(f'{YTDL} -o {new_out_template} {url}')
            proc.wait()

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
    Creates a directory browser widget with a label and set dir btn.
    """

    def __init__(self, *args, browser_starting_dir: AnyStr = None, **kwargs):
        super(BrowserWidget, self).__init__(*args, **kwargs)

        self.browser_starting_dir = browser_starting_dir

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.path_label = QLabel(self)
        main_layout.addWidget(self.path_label)

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
    Displays Yoink's video downloading controls.
    """

    def __init__(self, *args, **kwargs):
        super(DownloadWidget, self).__init__(*args, **kwargs)

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        form_layout = QFormLayout(self)
        main_layout.addLayout(form_layout)

        self.url_field = QPlainTextEdit(self)
        form_layout.addRow('download urls:'.title(), self.url_field)

        self.ext_combobox = QComboBox(self)
        self.ext_combobox.addItem('default'.title())
        self.ext_combobox.addItems(sorted(('avi', 'mkv', 'mp3', 'mp4', 'wav')))
        form_layout.addRow('output file type:'.title(), self.ext_combobox)

        self.browser_widget = BrowserWidget(self)
        form_layout.addRow('output directory:'.title(), self.browser_widget)

        self.download_button = QPushButton('download'.title(), self)
        self.download_button.setObjectName('download_button')
        main_layout.addWidget(self.download_button)

    def get_download_urls(self) -> List[AnyStr]:
        """
        :return:
            All urls in the url field
        """
        return [
            x for x in self.url_field.toPlainText().split('\n')
            if x
        ]

    def get_output_ext(self) -> AnyStr:
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

    def get_output_dir(self) -> AnyStr:
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

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')
        self.resize(600, 400)
        self.main_layout = QStackedLayout(self)
        self.setLayout(self.main_layout)

        self.download_widget = DownloadWidget(self)
        self.download_widget.download_button.clicked.connect(self.download)
        self.main_layout.addWidget(self.download_widget)

        self.loading_widget = LoadingWidget(self)
        self.main_layout.addWidget(self.loading_widget)

        self.runnable = YoinkRunnable()
        self.runnable.setAutoDelete(False)
        self.runnable.finished.signal.connect(
            lambda: self.main_layout.setCurrentIndex(0)
        )

    def download(self):
        """
        Starts downloading process using data gathered from the ui.
        """
        runnable = self.runnable
        runnable.urls = self.download_widget.get_download_urls()
        runnable.output_ext = self.download_widget.get_output_ext()
        runnable.output_dir = self.download_widget.get_output_dir()

        self.main_layout.setCurrentIndex(1)
        QThreadPool.globalInstance().start(runnable)


def main():

    import sys

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.setStyleSheet('''
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
        QComboBox:hover {
            background-color: rgb(0, 255, 255);
            color: black;
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
    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

    # import sys
    #
    # app = QApplication(sys.argv)
    # win = BrowserWidget()
    # win.show()
    # app.exec_()
