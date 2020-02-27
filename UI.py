
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QLabel,
    QHBoxLayout, QFileDialog
)


class Yoink(QWidget):

    _url_field = None
    _format_field = None
    _dir_browser = None

    def __init__(self, *args, **kwargs):
        super(Yoink, self).__init__(*args, **kwargs)

        self.setWindowTitle('Yoink')
        self.setFixedHeight(120)

        main_layout = QVBoxLayout()

        form_layout = QFormLayout()

        self._url_field = QLineEdit()
        form_layout.addRow(QLabel('URL'), self._url_field)

        self._format_field = QLineEdit()
        form_layout.addRow(QLabel('Format'), self._format_field)

        self._dir_browser = _DirBrowser()
        form_layout.addRow(QLabel('Output Dir'), self._dir_browser)

        main_layout.addLayout(form_layout)

        download_button = QPushButton('Download')
        download_button.clicked.connect(self.download)

        main_layout.addWidget(download_button)

        self.setLayout(main_layout)

    def download(self):
        print(self._url_field.text())
        print(self._format_field.text())
        print(self._dir_browser.dir_path)


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


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    win = Yoink()
    win.show()
    app.exec_()