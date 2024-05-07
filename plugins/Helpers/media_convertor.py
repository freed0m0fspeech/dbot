import subprocess


def convert_audio_file(file_path: str, extension: str = 'wav') -> str:
    """

    :param file_path: path to file
    :param extension: output extension
    :return: converted object bytes
    """

    output_path = file_path.replace(file_path.rsplit('.', 1)[1], extension)

    command = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', file_path, '-y', output_path]
    subprocess.run(command)
    return output_path