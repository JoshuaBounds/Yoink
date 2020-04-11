import os
import json
import warnings
from typing import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import youtube_dl


class BrowserWidget(QWidget):
    """
    Creates a directory browser widget that displays the currently
    selected directory location.
    """

    _path_label: QLabel = None
    _open_dir_browser_path: AnyStr = None

    def __init__(self, *args, **kwargs):
        super(BrowserWidget, self).__init__(*args, **kwargs)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._path_label = path_label = QLabel(self)
        main_layout.addWidget(path_label)

        browser_button = QPushButton('...', self)
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
            self._open_dir_browser_path or os.environ['userprofile'],
            QFileDialog.ShowDirsOnly
        )
        if path:
            self._path_label.setText(path)
            self._open_dir_browser_path = path
        return self._path_label.text()

    def get_path(self) -> AnyStr:
        """
        :return:
            Displayed directory location.
        """
        path = self._path_label.text()
        return os.path.isdir(path) and path or None

    def get_widget_preferences(self) -> Dict:
        """
        :return:
            Widget preferences data.
        """
        return {
            'path_label': self.get_path(),
            'open_dir_browser_path': self._open_dir_browser_path
        }

    def set_widget_preferences(self, data: Dict):
        """
        Sets widget preferences data.
        :param data:
            Preference data.
        """
        self._path_label.setText(
            data.get('path_label', os.environ['userprofile'])
        )
        self._open_dir_browser_path = (
            data.get('open_dir_browser_path', os.environ['userprofile'])
        )


class ParamWidget(QWidget):
    """
    Widget for editing youtube-dl parameters.
    """

    _param_field: QPlainTextEdit = None
    _open_load_preset_browser_path: AnyStr = None
    _open_save_preset_browser_path: AnyStr = None

    def __init__(self, *args, **kwargs):
        super(ParamWidget, self).__init__(*args, **kwargs)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        preset_layout = QHBoxLayout(self)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(preset_layout)

        load_preset_button = QPushButton('load preset', self)
        load_preset_button.clicked.connect(self.open_load_preset_browser)
        preset_layout.addWidget(load_preset_button)

        save_preset_button = QPushButton('save preset', self)
        save_preset_button.clicked.connect(self.open_save_preset_browser)
        preset_layout.addWidget(save_preset_button)

        self._param_field = param_field = QPlainTextEdit(self)
        param_field.setTabStopDistance(24)
        main_layout.addWidget(param_field)

    def get_widget_preferences(self) -> Dict:
        """
        :return:
            Widget preferences data.
        """
        return {
            'param_field':
                self._param_field.toPlainText(),
            'open_load_preset_browser_path':
                self._open_load_preset_browser_path,
            'open_save_preset_browser_path':
                self._open_save_preset_browser_path
        }

    def set_widget_preferences(self, data: Dict):
        """
        Sets widget preferences data.
        :param data:
            Preference data.
        """
        self._param_field.setPlainText(
            data.get('param_field', '')
        )
        self._open_load_preset_browser_path = (
            data.get(
                'open_load_preset_browser_path',
                os.environ['userprofile']
            )
        )
        self._open_save_preset_browser_path = (
            data.get(
                'open_save_preset_browser_path',
                os.environ['userprofile']
            )
        )

    def open_load_preset_browser(self) -> AnyStr:
        """
        Opens file browser to load a parameter preset.
        :return:
            Resulting file path from the file browser.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'open preset'.title(),
            self._open_load_preset_browser_path or os.environ['userprofile'],
            "JSON files (*.json);;Any (*)"
        )
        if file_path:
            try:
                with open(file_path) as f:
                    self._param_field.setPlainText(str(f.read()))
            except UnicodeDecodeError:
                warnings.warn('The target file could not be decoded')
            self._open_load_preset_browser_path = os.path.split(file_path)[0]
        return file_path

    def open_save_preset_browser(self) -> AnyStr:
        """
        Opens a file save browser to save the current parameter preset.
        :return:
            Resulting path from the file save browser.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'save preset'.title(),
            self._open_save_preset_browser_path,
            'JSON files (*.json);;Any (*)'
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self._param_field.toPlainText())
            self._open_save_preset_browser_path = os.path.split(file_path)[0]
        return file_path

    def get_params(self) -> Any:
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

    _path: AnyStr = None
    _start_dir: AnyStr = None

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
        print('urls:', self.urls)
        print('params:', self.params)
        print('output_dir:', self.output_dir)
        with ChangeDirectory(self.output_dir):
            with youtube_dl.YoutubeDL(self.params) as downloader:
                downloader.download(self.urls)
        self.finished.signal.emit()


class YoinkWidget(QWidget):
    """
    Yoink's main widget.
    """

    _main_layout: QStackedLayout = None
    _url_field: QPlainTextEdit = None
    _param_widget: ParamWidget = None
    _browser_widget: BrowserWidget = None
    _runnable: YoinkRunnable = None

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        # Widget

        self.setWindowTitle('Yoink')
        self.resize(600, 400)
        self.setFont(QFont('Consolas', -1, -1, False))
        self._main_layout = main_layout = QStackedLayout(self)
        self.setLayout(main_layout)

        # Download layout

        download_widget = QWidget(self)
        main_layout.addWidget(download_widget)

        download_layout = QVBoxLayout(download_widget)
        download_widget.setLayout(download_layout)

        form_layout = QFormLayout(download_widget)
        download_layout.addLayout(form_layout)

        self._url_field = url_field = QPlainTextEdit(download_widget)
        form_layout.addRow('urls'.title(), url_field)

        self._param_widget =param_widget = ParamWidget(download_widget)
        form_layout.addRow('download parameters'.title(), param_widget)

        self._browser_widget = browser_widget = BrowserWidget(download_widget)
        form_layout.addRow('output directory'.title(), browser_widget)

        download_button = QPushButton('download', download_widget)
        download_button.clicked.connect(self.yoink)
        download_layout.addWidget(download_button)

        # Loading layout

        loading_widget = QWidget(self)
        main_layout.addWidget(loading_widget)

        loading_layout = QVBoxLayout(loading_widget)
        loading_widget.setLayout(loading_layout)

        loading_label = QLabel('loading', loading_widget)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)

        # Runnable

        self._runnable = runnable = YoinkRunnable()
        runnable.setAutoDelete(False)
        runnable.finished.signal.connect(
            lambda: main_layout.setCurrentIndex(0)
        )

    def showEvent(self, QShowEvent):
        self.load_widget_preferences(self.DefaultPreferencesFilePath)

    def closeEvent(self, event: QCloseEvent):
        try:
            self.save_widget_preferences(self.DefaultPreferencesFilePath)
        except Exception as e:
            warnings.warn(e)
        super(YoinkWidget, self).closeEvent(event)

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

    def get_widget_preferences(self) -> Dict:
        """
        :return:
            Widget preferences data.
        """
        return {
            'url_field': self._url_field.toPlainText(),
            'param_widget': self._param_widget.get_widget_preferences(),
            'browser_widget': self._browser_widget.get_widget_preferences()
        }

    def set_widget_preferences(self, data: Dict):
        """
        Set widget preferences data.
        :param data:
            Preference data.
        """
        self._url_field.setPlainText(
            data.get('url_field', '')
        )
        self._param_widget.set_widget_preferences(
            data.get('param_widget', {})
        )
        self._browser_widget.set_widget_preferences(
            data.get('browser_widget', {})
        )

    def save_widget_preferences(self, file_path: AnyStr):
        """
        Saves the widgets current state to json file.
        :param file_path:
            File path.
        """
        with open(file_path, 'w') as f:
            f.write(json.dumps(self.get_widget_preferences(), indent=4))

    def load_widget_preferences(self, file_path: AnyStr):
        """
        Loads preferences from given json file path.
        :param file_path:
            Path to the json preferences file.
        """
        try:
            with open(file_path) as f:
                self.set_widget_preferences(json.loads(f.read()))
        except json.decoder.JSONDecodeError as e:
            warnings.warn('User preferences could not be loaded')
            warnings.warn(e)

    @property
    def DefaultPreferencesFilePath(self):
        """
        :return:
            Default preferences file path for Yoink.
        """
        return os.path.join(os.environ['appdata'], 'yoink.json')


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.show()

    sys.exit(app.exec_())
