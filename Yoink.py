import os
import json
from typing import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import youtube_dl


class BrowserWidget(QWidget):
    """
    Creates a directory browser widget that displays the currently
    selected directory location.
    """

    _path_field: QLineEdit = None

    def __init__(self, *args, **kwargs):
        super(BrowserWidget, self).__init__(*args, **kwargs)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._path_field = path_field = QLineEdit()
        path_field.setText(os.environ['userprofile'])
        path_field.setEnabled(False)
        main_layout.addWidget(path_field)

        browser_button = QPushButton('...')
        browser_button.clicked.connect(self.open_dir_browser)
        main_layout.addWidget(browser_button)

    def open_dir_browser(self):
        """
        Opens a file browser to set the widgets displayed directory.
        :return:
            Displayed file path.
        """
        path = QFileDialog.getExistingDirectory(
            self,
            'set output directory'.title(),
            self._path_field.text(),
            QFileDialog.ShowDirsOnly
        )
        path and self._path_field.setText(path)
        return self._path_field.text()

    def get_path(self):
        """
        :return:
            Displayed directory location.
        """
        path = self._path_field.text()
        return os.path.isdir(path) and path or None


class ParamWidget(QWidget):
    """
    Widget for editing youtube-dl parameters.
    """

    _param_field: QLineEdit = None

    def __init__(self, *args, **kwargs):
        super(ParamWidget, self).__init__(*args, **kwargs)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        preset_layout = QHBoxLayout()
        preset_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(preset_layout)

        load_preset_button = QPushButton('load preset')
        preset_layout.addWidget(load_preset_button)

        save_preset_button = QPushButton('save preset')
        preset_layout.addWidget(save_preset_button)

        self._param_field = param_field = QPlainTextEdit()
        param_field.setTabStopWidth(12)
        main_layout.addWidget(param_field)

    def get_params(self):
        """
        :return:
            Decoded Parameter data, or None if the data could not be
            decoded.
        """
        try:
            return json.loads(self._param_field.toPlainText())
        except json.decoder.JSONDecodeError:
            return None


class ChangeDirectory:
    """
    Context manager for temporarily changing python's current working
    directory.
    """

    _path = None
    _start_dir = None

    def __init__(self, path):
        """
        :param path:
             Path to the target working directory.
        """
        self._path = path

    def __enter__(self):
        os.path.isdir(self._path or '') and os.chdir(self._path)
        self._start_dir = os.getcwd()

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._start_dir)


class YoinkRunnable(QRunnable):
    """
    Performs the task of downloading video using the given data.
    """

    urls = None
    params = None
    output_dir = None

    class Emitter(QObject):
        signal: pyqtSignal = pyqtSignal()

    finished: Emitter = None

    def __init__(self, *args, **kwargs):
        super(YoinkRunnable, self).__init__(*args, **kwargs)
        self.finished = self.Emitter()

    def run(self):
        with ChangeDirectory(self.output_dir):
            with youtube_dl.YoutubeDL(self.params) as downloader:
                downloader.download(self.urls)
        self.finished.signal.emit()


class YoinkWidget(QWidget):
    """
    Yoink's main widget.
    """

    _main_layout: QStackedLayout = None
    _url_field: QLineEdit = None
    _param_widget: ParamWidget = None
    _browser_widget: BrowserWidget = None
    _runnable: YoinkRunnable = None

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self._main_layout = main_layout = QStackedLayout()
        self.setLayout(main_layout)

        # Download layout

        download_widget = QWidget()
        main_layout.addWidget(download_widget)

        download_layout = QVBoxLayout()
        download_widget.setLayout(download_layout)

        form_layout = QFormLayout()
        download_layout.addLayout(form_layout)

        self._url_field = url_field = QPlainTextEdit()
        form_layout.addRow('urls', url_field)

        self._param_widget =param_widget = ParamWidget()
        form_layout.addRow('params', param_widget)

        self._browser_widget = browser_widget = BrowserWidget()
        form_layout.addRow('output dir', browser_widget)

        download_button = QPushButton('download')
        download_button.clicked.connect(self.yoink)
        download_layout.addWidget(download_button)

        # Loading layout

        loading_widget = QWidget()
        main_layout.addWidget(loading_widget)

        loading_layout = QVBoxLayout()
        loading_widget.setLayout(loading_layout)

        loading_label = QLabel('loading')
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)

        # Runnable

        self._runnable = runnable = YoinkRunnable()
        runnable.setAutoDelete(False)
        runnable.finished.signal.connect(
            lambda: main_layout.setCurrentIndex(0)
        )

    def yoink(self):
        """
        Starts downloading process using data gathered from the gui.
        """
        runnable = self._runnable
        runnable.urls = self._url_field.toPlainText().split('\n')
        runnable.params = self._param_widget.get_params()
        runnable.output_dir = self._browser_widget.get_path()
        self._main_layout.setCurrentIndex(1)
        QThreadPool.globalInstance().start(runnable)


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.show()

    sys.exit(app.exec_())
