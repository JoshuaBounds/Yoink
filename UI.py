"""
TODO
    Multi threading to keep window from freezing.
    Loading bar, console, or logging file.
    Better ffmpeg format support.
"""


import os
from tempfile import TemporaryDirectory
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QLabel,
    QHBoxLayout, QFileDialog, QPlainTextEdit
)
import youtube_dl
import ffmpy3


class _DirBrowser(QWidget):

    _dir_path = os.environ['USERPROFILE']
    _path_field = None

    def __init__(self, *args, **kwargs):
        super(_DirBrowser, self).__init__(*args, **kwargs)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._path_field = QLineEdit(self.dir_path)
        self._path_field.setEnabled(False)
        main_layout.addWidget(self._path_field)

        search_button = QPushButton('...')
        search_button.clicked.connect(self.open_browser)
        main_layout.addWidget(search_button)

        self.setLayout(main_layout)

    @property
    def dir_path(self):
        return self._dir_path

    @dir_path.setter
    def dir_path(self, path):
        self._dir_path = path
        self._path_field.setText(path)

    def open_browser(self):
        self.dir_path = QFileDialog.getExistingDirectory(
            self,
            'Open Directory',
            self.dir_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )


class Yoink(QWidget):

    _urls_field = None
    _ff_formats_field = None
    _dir_browser = None

    download_params = {'outtmpl': '%(title)s'}

    def __init__(self, *args, **kwargs):
        super(Yoink, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()

        self._urls_field = QPlainTextEdit()
        form_layout.addRow(QLabel('Input URLs'), self._urls_field)

        self._ff_formats_field = QPlainTextEdit()
        form_layout.addRow(QLabel('Output Formats'), self._ff_formats_field)

        self._dir_browser = _DirBrowser()
        form_layout.addRow(QLabel('Output Directory'), self._dir_browser)

        main_layout.addLayout(form_layout)

        download_button = QPushButton('Download')
        download_button.clicked.connect(self.download)

        main_layout.addWidget(download_button)

        self.setLayout(main_layout)

    def download(self):

        urls = self._urls_field.toPlainText().split('\n')
        ff_formats = self._ff_formats_field.toPlainText().split('\n')
        output_directory = self._dir_browser.dir_path
        current_working_directory = os.getcwd()

        with TemporaryDirectory() as t:

            os.chdir(t)

            for url, ff_format in zip(urls, ff_formats):

                if not ff_format.startswith('.'):
                    continue

                with youtube_dl.YoutubeDL(self.download_params) as y:
                    y.download([url])

                for file_path in os.listdir(t):

                    if not os.path.isfile(file_path):
                        continue

                    _, file_name = os.path.split(file_path)
                    name, extension = os.path.splitext(file_name)
                    new_file_path = os.path.join(
                        output_directory,
                        name + ff_format
                    )

                    if os.path.exists(new_file_path):
                        continue

                    x = ffmpy3.FFmpeg(
                        inputs={file_path: None},
                        outputs={new_file_path: None}
                    )
                    x.run()

            os.chdir(current_working_directory)


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = Yoink()
    win.show()
    app.exec_()