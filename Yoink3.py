
import os
from typing import *
from tempfile import TemporaryDirectory
from subprocess import Popen


def download(url: AnyStr) -> NoReturn:
    cmd = 'youtube-dl.exe %s --output %%(title)s.%%(ext)s' % url
    process = Popen(cmd)
    process.wait()


def convert(input: AnyStr, output: AnyStr) -> NoReturn:
    cmd = 'ffmpeg.exe -i "%s" "%s"' % (input, output)
    process = Popen(cmd)
    process.wait()


def convert_directory(source_dir, output_dir, extension):

    for file_name in os.listdir(source_dir):

        file_path           = os.path.join(source_dir, file_name)
        name, _             = os.path.splitext(file_name)
        output_file_path    = os.path.join(output_dir, name) + extension

        convert(file_path, output_file_path)


def yoink(url, extension, output_dir):

    with TemporaryDirectory() as temp_dir, CheckpointCurrentDirectory():
        os.chdir(temp_dir)
        download(url)
        convert_directory(temp_dir, output_dir, extension)


class CheckpointCurrentDirectory:

    checkpoint_directory: AnyStr = None

    def __enter__(self):
        self.checkpoint_directory = os.getcwd()

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.checkpoint_directory)


if __name__ == '__main__':

    yoink(
        r"https://www.youtube.com/playlist?list=PLPWrQVjtip4envhILBNp8Bmwff30UF1Vp",
        '.mp3',
        r"C:\Users\jboun\Desktop\test"
    )
