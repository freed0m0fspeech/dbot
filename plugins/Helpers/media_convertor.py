import subprocess


def convert_audio_file(path: str, extension: str = '.wav', output_path: str = '') -> str:
    """

    :param path: input file path
    :param extension: output file extension
    :param output_path: output file path
    :return: output_path
    """
    if not output_path:
        output_path = path.replace('.ogg', extension)

    # -loglevel error -hide_banner -nostats
    # stderr=subprocess.DEVNULL for silent mode

    command = ['ffmpeg', '-i', path, output_path]
    subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    return output_path
