"""
Youtube downloader and file converter.
Requires environment to contain youtube-dl.exe and ffmpeg.exe
"""


import os
from typing         import *
from tempfile       import TemporaryDirectory
from subprocess     import Popen


__all__ = 'download', 'convert', 'convert_dir', 'yoink'


def download(url: AnyStr, dst_dir: AnyStr) -> NoReturn:
    """
    Alias wrapper function for youtube-dl.
    Downloads videos contained in the given url to the target directory.
    :param url:
        Youtube url. Can be video, or playlist.
    :param dst_dir:
        Destination directory for the downloaded videos.
    """

    # Creates the command for the youtube-dl subprocess.
    cmd = (
        r'youtube-dl.exe %s' % url
        + r' --output %s\%%(title)s.%%(ext)s' % dst_dir
    )

    # Runs the youtube-dl subprocess.
    process = Popen(cmd)
    process.wait()


def convert(in_path: AnyStr, out_path: AnyStr) -> NoReturn:
    """
    Converts given input file path to the given output file path.
    The extension of the output file path defines the resulting
    converted file type.
    :param in_path:
        Path to the input file.
    :param out_path:
        Path of the desired output file. Extension will determine the
        resulting file type.
    """

    # Creates the command for the ffmpeg subprocess.
    cmd = 'ffmpeg.exe -i "%s" "%s"' % (in_path, out_path)

    # Runs the ffmpeg subprocess.
    process = Popen(cmd)
    process.wait()


def convert_dir(src_dir: AnyStr, out_dir: AnyStr, ext: AnyStr) -> NoReturn:
    """
    Converts every file in the given directory to the given file type at
    the given output directory.
    :param src_dir:
        Directory of files to convert.
    :param out_dir:
        Directory for the resulting converted files.
    :param ext:
        Extension which defines the converted file type.
    """

    # Gets all files in the given source dir.
    for file_name in os.listdir(src_dir):

        # Generates the target file path, and the destination file path.
        file_path           = os.path.join(src_dir, file_name)
        name, _             = os.path.splitext(file_name)
        output_file_path    = os.path.join(out_dir, name) + ext

        # Converted the file.
        convert(file_path, output_file_path)


def yoink(url: AnyStr, ext: AnyStr, out_dir: AnyStr) -> NoReturn:
    """
    Downloads and converts all videos from the given url to the given
    file extension type with the results going to the given output
    directory.
    :param url:
        Youtube url. Can be video or playlist.
    :param ext:
        Desired output file extension. This will define the converted
        output file type.
    :param out_dir:
        The output directory for all converted files.
    """

    # Creates a temporary directory for the raw downloaded videos.
    with TemporaryDirectory() as temp_dir:

        # Downloads videos into the temporary directory.
        download(url, temp_dir)

        # Converts all videos in the temporary directory with the output
        # going to the given output directory.
        convert_dir(temp_dir, out_dir, ext)


if __name__ == '__main__':

    url         = input('Download URL:')
    extension   = input('Output file type extension:')
    output_dir  = input('Output directory:')

    yoink(url, extension, output_dir)
