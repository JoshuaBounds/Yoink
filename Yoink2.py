
from typing import *
import os
import subprocess
import tempfile


YOUTUBE_DL_NAME = 'youtube-dl.exe'
FFMPEG_NAME = 'ffmpeg.exe'


class Yoink:

    class CheckpointCurrentDirectory:

        checkpoint_directory: AnyStr = None

        def __enter__(self):
            self.checkpoint_directory = os.getcwd()

        def __exit__(self, exc_type, exc_val, exc_tb):
            os.chdir(self.checkpoint_directory)

    @staticmethod
    def iterate_iterables(iterables: Iterable[Iterable]) -> Generator:
        return (
            item
            for iterable in iterables
            for item in iterable
        )

    @classmethod
    def get_youtube_dl_process(
            cls,
            args: Iterable[AnyStr]
    ) -> subprocess.Popen:
        command = (
            ' '.join(
                cls.iterate_iterables(
                    ([YOUTUBE_DL_NAME], args)
        )))
        return subprocess.Popen(command)

    @classmethod
    def get_ffmpeg_process(cls, args: Iterable[AnyStr]) -> subprocess.Popen:
        command = (
            ' '.join(
                cls.iterate_iterables(
                    ([FFMPEG_NAME], args)
        )))
        return subprocess.Popen(command)

    @classmethod
    def get_download_process(
            cls,
            urls: Iterable[AnyStr],
            args: Iterable[AnyStr] = None
    ) -> subprocess.Popen:
        return (
            cls.get_youtube_dl_process(
                cls.iterate_iterables(
                    (args or [], urls)
        )))

    @classmethod
    def get_convert_process(
            cls,
            input_file_path: AnyStr,
            output_file_path: AnyStr,
            global_args: Iterable[AnyStr] = None,
            input_args: Iterable[AnyStr] = None,
            output_args: Iterable[AnyStr] = None
    ) -> subprocess.Popen:
        return (
            cls.get_ffmpeg_process(
                cls.iterate_iterables(
                    (
                        global_args or [],
                        input_args or [],
                        ['-i "%s"' % input_file_path],
                        output_args or [],
                        ['"%s"' % output_file_path]
                    )
        )))

    @classmethod
    def yoink(
            cls,
            urls: Iterable[AnyStr],
            output_extension: AnyStr,
            output_directory: AnyStr,
            dl_args: Iterable[AnyStr] = None
    ) -> None:

        tmp_dir = tempfile.TemporaryDirectory()
        cp_dir = cls.CheckpointCurrentDirectory()
        with tmp_dir as working_directory, cp_dir:

            os.chdir(working_directory)
            cls.get_download_process(urls, dl_args).wait()

            for file_name in os.listdir(working_directory):

                file_path = os.path.join(working_directory, file_name)

                name, _ = os.path.splitext(file_name)
                output_file_name = '.'.join((name, output_extension))
                output_file_path = os.path.join(
                    output_directory,
                    output_file_name
                )
                cls.get_convert_process(file_path, output_file_path).wait()


if __name__ == '__main__':
    user_input = [input('download url: ')]
    Yoink.yoink(user_input, 'mp3', os.getcwd(), ['-o %(title)s.%(ext)s'])
