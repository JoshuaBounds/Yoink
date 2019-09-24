import shutil
import os
import tempfile
import re
from typing import AnyStr, Iterable
import youtube_dl
import ffmpy3


def yoink(
        urls: Iterable[AnyStr],
        out_dir: AnyStr,
        out_type: AnyStr = ...,
        out_flags: AnyStr = None,
):

    with tempfile.TemporaryDirectory() as temp_dir:

        start_dir = os.getcwd()
        os.chdir(temp_dir)

        downloader = youtube_dl.YoutubeDL({'outtmpl': '%(title)s.%(ext)s'})
        downloader.download(urls)

        if out_type is not ...:
            re_file_extension = re.compile(r'[^.]+$')
            for downloaded_file in os.scandir(os.curdir):
                file_name = os.path.basename(downloaded_file.path)
                output_name = re_file_extension.sub(out_type, file_name)
                converter = ffmpy3.FFmpeg(
                    inputs={file_name: None},
                    outputs={output_name: out_flags},
                )
                converter.run()
                os.remove(downloaded_file)

        for resulting_file in os.scandir(os.curdir):
            shutil.move(
                resulting_file,
                os.path.join(out_dir, os.path.basename(resulting_file)),
            )

        os.chdir(start_dir)


if __name__ == '__main__':

    yoink(
        [
            'https://www.youtube.com/watch?v=mw3if4nIA8A',
            'https://www.youtube.com/watch?v=ArxkZq-4NQE',
        ],
        os.path.join(os.environ['USERPROFILE'], 'Desktop'),
        'mp3'
    )
