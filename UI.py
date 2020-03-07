"""
TODO
    _YoinkModel having difficulty with the setData method
    Multi threading to keep window from freezing.
    Loading bar, console, or logging file.
    Better ffmpeg format support.
"""


import os
from typing import Any, AnyStr, Dict, Iterable, List
from tempfile import TemporaryDirectory
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QLabel,
    QHBoxLayout, QFileDialog, QPlainTextEdit, QTableView
)
from PyQt5.QtCore import QThread, QRunnable, QThreadPool, QAbstractTableModel, QModelIndex, Qt, QVariant
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
    def dir_path(self) -> AnyStr:
        return self._dir_path

    @dir_path.setter
    def dir_path(self, path: AnyStr):
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


class YoinkModel(QAbstractTableModel):

    table: Dict = {}
    rows: int = 0
    columns: int = 0

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        return self.rows

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        return self.columns

    def data(self, index: QModelIndex, role: int = None):
        if role == Qt.DisplayRole:
            column = self.table.get(index.row(), {})
            return column.get(index.column(), QVariant())
        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = None):
        if role == Qt.EditRole:
            if not self.checkIndex(index):
                return False
            self.table.setdefault(index.row(), {})[index.column()] = value
            return True
        return False

    def flags(self, index: QModelIndex):
        return Qt.ItemIsEditable | QAbstractTableModel.flags(self, index)


class Yoink(QWidget):

    _dir_browser = None

    download_params: Dict = {'outtmpl': '%(title)s'}

    def __init__(self, *args, **kwargs):
        super(Yoink, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')

        main_layout = QVBoxLayout()

        view = QTableView()
        view.setModel(YoinkModel())
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

    # win = Yoink()
    # win.show()

    win = QTableView()
    model = YoinkModel()
    model.rows = 2
    model.columns = 5
    win.setModel(model)
    win.show()

    app.exec_()
