from typing import Any, AnyStr, List, Union
from tempfile import TemporaryDirectory
import os
import shutil
import json
from PyQt5.Qt import Qt
from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QTextEdit, QStackedLayout, QLabel
import youtube_dl
import ffmpy3


class Yoink:
    """
    Youtube-DL and FFMPEG tool for downloading and converting youtube
    videos.
    """

    dl_urls: List = None
    dl_params: Any = None
    ff_output_ext: AnyStr = None
    ff_in_params: Any = None
    ff_out_params: Any = None
    output_dir: AnyStr = None

    class ChangeDir:
        """
        Context manager that Temporarily changes the working directory
        to `directory` before returning to the initial current working
        directory.
        """

        working_dir: AnyStr = None
        starting_dir: AnyStr = None

        def __init__(self, directory: AnyStr):
            """
            :param directory:
                Target directory to change the current working directory
                to.
            """
            if not os.path.isdir(directory):
                raise FileExistsError('`directory` is invalid')
            self.working_dir = directory

        def __enter__(self):
            self.starting_dir = os.getcwd()
            os.chdir(self.working_dir)
            return self.starting_dir

        def __exit__(self, exc_type, exc_val, exc_tb):
            os.chdir(self.starting_dir)

    @staticmethod
    def download(urls: List = None, params: Any = None):
        """
        youtube_dl wrapper.
        :param urls:
            URls of youtube videos to download.
        :param params:
            Youtube-DL parameters.
        """
        with youtube_dl.YoutubeDL(params) as y:
            y.download(urls)

    @staticmethod
    def convert(inputs, outputs):
        """
        ffmpy3 wrapper.
        :param inputs:
            Equivalent to ffmpy3.FFmpeg(inputs=...).
        :param outputs:
            Equivalent to ffmpy3.FFmpeg(outputs=...).
        """
        converter = ffmpy3.FFmpeg(inputs=inputs, outputs=outputs)
        converter.run()

    @classmethod
    def convert_directory(
            cls,
            src: AnyStr,
            dst: AnyStr,
            output_ext,
            in_params,
            out_params
    ):
        """
        Performs `convert` on all files in `src` with the results going
        to `dst`.
        Output files will overwrite existing files.
        Raises FileNoteFound if either `src` or `dst` are an
        invalid location.
        :param src:
            Source directory to convert files from.
        :param dst:
            Destination of the converted files.
        :param output_ext:
            Extension given to the converted files. This also determines
            the file's type.
        :param in_params:
            Input parameters given to each converted file.
            Equivalent to ffmpy3.FFmpeg(inputs={FILE: ...}).
        :param out_params:
            Output parameters given to each converted file.
            Equivalent to ffmpy3.FFmpeg(outputs={FILE: ...}).
        """

        if not os.path.isdir(src):
            raise FileNotFoundError('Invalid location given for `src`')
        if not os.path.isdir(dst):
            raise FileNotFoundError('Invalid location given for `dst`')

        file_paths = (
            (os.path.join(src, file_name), os.path.join(dst, file_name))
            for file_name in os.listdir(src)
        )
        for src_file_path, dst_file_path in file_paths:
            new_dst_file_path = (
                os.path.splitext(dst_file_path)[0] + output_ext
                if output_ext else
                dst_file_path
            )
            if os.path.isfile(new_dst_file_path):
                os.remove(new_dst_file_path)
            cls.convert(
                {src_file_path: in_params},
                {new_dst_file_path: out_params}
            )

    def yoink(self):
        """
        Downloads and converts videos using class attributes:
            dl_urls: List
            dl_params: Any
            ff_output_ext: AnyStr
            ff_in_params: Any
            ff_out_params: Any
            output_dir: AnyStr
        """

        if not isinstance(self.dl_urls, list):
            raise ValueError('`dl_urls` must be a list')

        td = TemporaryDirectory
        cd = self.ChangeDir
        with td() as working_dir, cd(working_dir) as starting_dir:

            self.download(self.dl_urls, self.dl_params)

            if self.ff_output_ext or self.ff_out_params:

                self.convert_directory(
                    working_dir,
                    self.output_dir or starting_dir,
                    self.ff_output_ext,
                    self.ff_in_params,
                    self.ff_out_params
                )

            else:

                for file_name in os.listdir(working_dir):
                    path = os.path.join(
                        self.output_dir or starting_dir,
                        file_name
                    )
                    shutil.move(file_name, path)

            os.chdir(starting_dir)


class YoinkRunnable(QRunnable, Yoink):
    """
    QRunnable version of `Yoink`.
    """

    class Emitter(QObject):
        signal: pyqtSignal = pyqtSignal()

    finished: Emitter = None

    def __init__(self, *args, **kwargs):
        super(YoinkRunnable, self).__init__(*args, **kwargs)
        self.finished = self.Emitter()

    def run(self):
        self.yoink()
        self.finished.signal.emit()


class YoinkWidget(QWidget, Yoink):
    """
    QWidget version of `Yoink`.
    """

    _main_layout: QStackedLayout = None
    _dl_urls: QTextEdit = None
    _dl_params: QTextEdit = None
    _ff_output_ext: QLineEdit = None
    _ff_in_params: QTextEdit = None
    _ff_out_params: QTextEdit = None
    _download: QPushButton = None
    _runnable: YoinkRunnable = None

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self._main_layout = main_layout = QStackedLayout()
        self.setLayout(main_layout)

        yoink_widget = QWidget()
        main_layout.addWidget(yoink_widget)
        yoink_layout = QVBoxLayout()
        yoink_widget.setLayout(yoink_layout)
        form_layout = QFormLayout()
        yoink_layout.addLayout(form_layout)
        self._dl_urls = dl_urls = QTextEdit()
        form_layout.addRow('dl urls', dl_urls)
        self._ff_output_ext = ff_output_ext = QLineEdit()
        form_layout.addRow('ff output ext', ff_output_ext)
        self._output_dir = output_dir = QLineEdit()
        form_layout.addRow('output dir', output_dir)
        self._dl_params = dl_params = QTextEdit()
        form_layout.addRow('dl params', dl_params)
        self._ff_in_params = ff_in_params = QTextEdit()
        form_layout.addRow('ff in params', ff_in_params)
        self._ff_out_params = ff_out_params = QTextEdit()
        form_layout.addRow('ff out params', ff_out_params)
        self._download = download = QPushButton('Download')
        download.clicked.connect(self.yoink)
        yoink_layout.addWidget(download)

        loading_widget = QWidget()
        main_layout.addWidget(loading_widget)
        loading_layout = QVBoxLayout()
        loading_widget.setLayout(loading_layout)
        loading_label = QLabel('Loading...')
        loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_label)

        self._runnable = YoinkRunnable()
        self._runnable.setAutoDelete(False)
        self._runnable.finished.signal.connect(
            lambda: self._main_layout.setCurrentIndex(0)
        )

    @staticmethod
    def exec_json_loads(data: AnyStr) -> Union[Any, None]:
        """
        Wrapper for json.loads that returns `None` instead of raising a
        `json.decoder.JSONDecodeError`.
        """
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            return None

    def yoink(self):
        """
        Runs yoink using data gathered from the Widget's UI. During this
        time the UI cannot be used until the yoink process finishes.
        """

        self._runnable.dl_urls = [
            x for x in map(str.strip, self._dl_urls.toPlainText().split('\n'))
            if x
        ]
        self._runnable.ff_output_ext = self._ff_output_ext.text().strip()
        self._runnable.output_dir = self._output_dir.text().strip()
        self._runnable.dl_params = self.exec_json_loads(
            self._dl_params.toPlainText()
        )
        self._runnable.ff_in_params = self.exec_json_loads(
            self._ff_in_params.toPlainText()
        )
        self._runnable.ff_out_params = self.exec_json_loads(
            self._ff_out_params.toPlainText()
        )

        if not os.path.isdir(self._runnable.output_dir):
            print('Invalid output directory')
            return None

        self._main_layout.setCurrentIndex(1)

        thread_pool = QThreadPool.globalInstance()
        thread_pool.start(self._runnable)


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.show()

    sys.exit(app.exec_())
