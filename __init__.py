from typing import Any, AnyStr, List
from tempfile import TemporaryDirectory
import os
import shutil
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QFormLayout, QTextEdit
import youtube_dl
import ffmpy3


class Yoink:

    dl_urls: List = None
    dl_params: Any = None
    ff_output_ext: AnyStr = None
    ff_in_params: Any = None
    ff_out_params: Any = None
    output_dir: AnyStr = None

    class ChangeDir:

        working_dir: AnyStr = None
        starting_dir: AnyStr = None

        def __init__(self, working_dir):
            if not os.path.isdir(working_dir):
                raise FileExistsError('`working_dir` does not exist')
            self.working_dir = working_dir

        def __enter__(self):
            self.starting_dir = os.getcwd()
            os.chdir(self.working_dir)
            return self.starting_dir

        def __exit__(self, exc_type, exc_val, exc_tb):
            os.chdir(self.starting_dir)

    @staticmethod
    def exec_json_loads(data):
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            return None

    @staticmethod
    def download(dl_urls, dl_params):
        with youtube_dl.YoutubeDL(dl_params) as y:
            y.download(dl_urls)

    @staticmethod
    def convert(inputs, outputs):
        converter = ffmpy3.FFmpeg(inputs=inputs, outputs=outputs)
        converter.run()

    @classmethod
    def convert_directory(cls, src, dst, output_ext, in_params, out_params):

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

        if not self.dl_urls:
            return None

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


class YoinkWidget(QWidget, Yoink):

    _dl_urls: QTextEdit = None
    _dl_params: QTextEdit = None
    _ff_output_ext: QLineEdit = None
    _ff_in_params: QTextEdit = None
    _ff_out_params: QTextEdit = None
    _download: QPushButton = None

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout(self)
        layout.addLayout(form_layout)
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
        download.clicked.connect(self._yoink)
        layout.addWidget(download)

    def _yoink(self):
        self.dl_urls = [
            x for x in map(str.strip, self._dl_urls.toPlainText().split('\n'))
            if x
        ]
        self.ff_output_ext = self._ff_output_ext.text().strip()
        self.output_dir = self._output_dir.text().strip()
        self.dl_params = self.exec_json_loads(self._dl_params.toPlainText())
        self.ff_in_params = self.exec_json_loads(self._ff_in_params.toPlainText())
        self.ff_out_params = self.exec_json_loads(self._ff_out_params.toPlainText())

        print(list(self.dl_urls))
        print(self.ff_output_ext)
        print(self.output_dir)
        print(self.dl_params)
        print(self.ff_in_params)
        print(self.ff_out_params)

        self.yoink()


if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    win = YoinkWidget()
    win.show()

    sys.exit(app.exec_())
