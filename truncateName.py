import sys
import os
import pandas
import xlwings as xw

# maximum file name length
MAX_NAME = 30

def truncate_name(dirs, max=MAX_NAME):
    """Construct new file name from the end to the front until it exceeds MAX_NAME.

     Args:
        dirs: list of directory names ["tag1", "tag2", ..., "tagN", file].
        max: integer maximum length for file name.
     Returns:
        String: file name shorter than MAX_NAME
    """
    new_filename = os.path.sep.join(dirs)
    length = len(new_filename)
    num_split = 1
    while length > max:
        # split off front num_split directories
        split = new_filename.split(new_filename, num_split)
        length = len(split[-1])
        num_split += 1
        new_filename = split[-1]
    return new_filename

name = truncate_name(["omero/omeroTest/truncateName.py"])
print(name)