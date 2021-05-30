
import os
import contextlib

@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """
    A context manager to temporarily redirect stdout or stderr

    From https://stackoverflow.com/questions/7018879/disabling-output-when-compiling-with-distutils
    """

    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, 'w+')
        os.dup2(dest_file.fileno(), stdchannel.fileno())

        yield dest_file
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
        if dest_file is not None:
            dest_file.close()