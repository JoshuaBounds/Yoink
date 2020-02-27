
import os
import shutil
from tempfile import TemporaryDirectory
import ffmpy3
import youtube_dl


def download(destination_dir, *urls, output_extension=..., output_ffmpeg=...):

    starting_dir = os.getcwd()

    with TemporaryDirectory() as temp_dir:

        os.chdir(temp_dir)

        with youtube_dl.YoutubeDL() as downloader:
            downloader.download(urls)

        for video in os.listdir(temp_dir):

            name, extension = os.path.splitext(video)
            new_filename = name + output_extension

            ffmpy3.FFmpeg(
                inputs={video: None},
                outputs={new_filename: output_ffmpeg}
            )

        shutil.copytree(temp_dir, destination_dir, dirs_exist_ok=True)

        os.chdir(starting_dir)


if __name__ == '__main__':

    urls = [
        'https://www.youtube.com/watch?v=3O7fK7oWVTg',
        'https://www.youtube.com/watch?v=wDXei_Hgmqo&list=PLPWrQVjtip4cvs77owSKttv1bxS_UNjmX'
    ]

    download(r"C:\Users\Joshua\Desktop\something", *urls)
