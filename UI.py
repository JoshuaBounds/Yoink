"""
TODO
    _YoinkModel having difficulty with the setData method
    Multi threading to keep window from freezing.
    Loading bar, console, or logging file.
    Better ffmpeg format support.
"""


import os
from typing import AnyStr, Dict, Iterable
from tempfile import TemporaryDirectory
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QLabel,
    QHBoxLayout, QFileDialog, QPlainTextEdit, QTableView
)
from PyQt5.QtCore import QThread, QRunnable, QThreadPool, QAbstractItemModel, QModelIndex, Qt
import youtube_dl
import ffmpy3


_QModelIndex = QModelIndex


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


class _Download(QRunnable):

    urls: Iterable[AnyStr] = None
    download_params: Dict = {}

    def run(self):
        with youtube_dl.YoutubeDL(self.download_params) as y:
            y.download(self.urls)


class _Convert(QRunnable):

    inputs: Dict = {}
    outputs: Dict = {}

    def run(self):
        converter = ffmpy3.FFmpeg(inputs=self.inputs, outputs=self.outputs)
        converter.run()


class _YoinkView(QTableView):
    pass


class _YoinkModel(QAbstractItemModel):

    table = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.table)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.table[0])

    def index(self, p_int, p_int_1, parent=None, *args, **kwargs):
        return self.createIndex(p_int, p_int_1, self.table[p_int][p_int_1])

    def hasChildren(self, parent=None, *args, **kwargs):
        return False

    def parent(self, QModelIndex=None):
        return _QModelIndex()

    def data(self, QModelIndex, role=None):
        if role == Qt.DisplayRole and QModelIndex.isValid():
            return self.table[QModelIndex.row()][QModelIndex.column()]

    def setData(self, QModelIndex, Any, role=None):
        if role == Qt.EditRole and QModelIndex.isValid():
            self.table[QModelIndex.row()][QModelIndex.column()] = Any
            self.dataChanged.emit(QModelIndex, QModelIndex, [role])

    def flags(self, QModelIndex):
        if QModelIndex.isValid():
            return Qt.ItemIsEditable | Qt.ItemIsEnabled



class Yoink(QWidget):

    _dir_browser = None

    download_params = {'outtmpl': '%(title)s'}

    def __init__(self, *args, **kwargs):
        super(Yoink, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')

        main_layout = QVBoxLayout()

        view = _YoinkView()
        view.setModel(_YoinkModel())

        main_layout.addWidget(view)

        download_button = QPushButton('Download')

        main_layout.addWidget(download_button)

        self.setLayout(main_layout)


# for file_path in os.listdir(t):
#
#     if not os.path.isfile(file_path):
#         continue
#
#     _, file_name = os.path.split(file_path)
#     name, extension = os.path.splitext(file_name)
#     new_file_path = os.path.join(
#         self.output_directory,
#         name + ff_format
#     )
#
#     if os.path.exists(new_file_path):
#         continue
#
#     x = ffmpy3.FFmpeg(
#         inputs={file_path: None},
#         outputs={new_file_path: None}
#     )
#     x.run()


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = Yoink()
    win.show()
    app.exec_()