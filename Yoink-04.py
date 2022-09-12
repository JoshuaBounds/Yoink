import os
import fnmatch
from PyQt5 import QtWidgets
import ffmpeg
import yt_dlp


class DirBrowserWidget(QtWidgets.QWidget):
    """
    Displays the current path, and a button to open a dir browser to set
    the current path.
    """

    def __init__(self, *args, starting_dir=None, **kwargs):
        """
        :param starting_dir:
            Init the widget with this path as default.
            If not given, is set to cwd.
        """
        super(DirBrowserWidget, self).__init__(*args, **kwargs)

        self.starting_dir = starting_dir or os.getcwd()

        self.setLayout(QtWidgets.QHBoxLayout())

        self.path_txf = QtWidgets.QLabel(self.starting_dir)
        self.layout().addWidget(self.path_txf)

        browser_btn = QtWidgets.QPushButton('browse'.title())
        browser_btn.setMaximumWidth(80)
        browser_btn.clicked.connect(self.open_dir_browser)
        self.layout().addWidget(browser_btn)

    @property
    def path(self):
        return self.path_txf.text()

    def open_dir_browser(self):
        """
        Opens a dir browser to set the widgets displayed directory.
        :return:
            Selected dir path.
        """
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'set output directory'.title(),
            self.starting_dir,
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if path:
            self.path_txf.setText(path)
            self.starting_dir = path
        return self.path_txf.text()


class YoinkWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(YoinkWidget, self).__init__(*args, **kwargs)

        self.setLayout(QtWidgets.QVBoxLayout())

        # Downloader
        self.dir_browser = DirBrowserWidget()
        self.dir_browser.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.dir_browser)

        self.urls_txe = QtWidgets.QPlainTextEdit()
        self.layout().addWidget(self.urls_txe)

        download_btn = QtWidgets.QPushButton('download'.title())
        download_btn.clicked.connect(self.download)
        self.layout().addWidget(download_btn)

        # Converter
        convert_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(convert_layout)

        self.convert_src_txf = QtWidgets.QLineEdit()
        convert_layout.addWidget(self.convert_src_txf)

        self.convert_dst_txf = QtWidgets.QLineEdit()
        convert_layout.addWidget(self.convert_dst_txf)

        convert_btn = QtWidgets.QPushButton('Convert')
        convert_btn.clicked.connect(self.convert)
        self.layout().addWidget(convert_btn)

    def download(self):
        urls = [x for x in self.urls_txe.toPlainText().split('\n') if x]
        opts = {'outtmpl': os.path.join(self.dir_browser.path, '%(title)s.%(ext)s')}
        with yt_dlp.YoutubeDL(opts) as downloader:
            downloader.download(urls)

    def convert(self):
        dir_path = self.dir_browser.path
        src_txt = self.convert_src_txf.text()
        dst_txt = self.convert_dst_txf.text()
        for filename in fnmatch.filter(os.listdir(dir_path), src_txt):
            if os.path.isdir(os.path.join(dir_path, filename)):
                continue
            new_name = os.path.splitext(filename)[0] + dst_txt
            (
                ffmpeg
                .input(os.path.join(dir_path, filename))
                .output(os.path.join(dir_path, new_name))
                .run()
            )


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = YoinkWidget()
    win.show()
    app.exec_()


if __name__ == '__main__':
    main()
