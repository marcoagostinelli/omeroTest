import sys
import os
import pandas as pd
import xlwings as xw
from HTD_practice import getHtdFile
from regexTest import getImages
from regexTest import getIncompleteWells
from regexTest import getValidImageNames
from regexTest import checkName
import json
#TODO uncomment this line when omero is installed on python
#from regexTest import checkName
import re

# maximum file name length
MAX_NAME = 255
# TODO: replace \\ with os.path.sep
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
        split = new_filename.split(os.path.sep, num_split)
        length = len(split[-1])
        num_split += 1
    new_filename = split[-1]
    return new_filename

def walk_files(root, extensions):
    """Navigates each file and folder beginning at the root folder and checks for image files.

    Args:
        root: path of the root project folder.
        extensions: list of string image file extensions.
    Yields:
        Yields file name and file path of each image file found.
    Raises:
    """
    for dirpath, dirnames, files in os.walk(root, topdown=True):
        for file in files:
            timepoint,zStep = getTandZ(dirpath)
            filename, extension = os.path.splitext(file)
            if extension in extensions:
                filepath = os.path.join(dirpath, file)
                # get accompanying json file
                json = None
                for f in os.listdir(dirpath):
                    name, ext = os.path.splitext(f)
                    if (ext == ".json") and (name.lower().count(file.lower()) > 0):
                        json = f
                
                yield (file, filepath, json, timepoint, zStep)
    


def create_DataFrame(root,valid, extensions,htd, columns=["Well_Name","IMAGE NAME","File Name","File Path","MMA FILE PATH","Site ID", "Wavelength ID", "Z Score", "TimePoint"]):
    """Create a DataFrame containing image file info for the root directory.

    DataFrame will contain file name, new file name constructed by replacing backslashes in filepath
    with underscores, file path, MMA file path for the accompanying json file path, and tags which are the root directories subdirectories seperated by hashtags.

     Args:
        root: path to a dataset directory continaing subdirectories and image files.
        valid: a list of valid image names. Only images in this list will be added to the excel file
        extensions: list of string image file extensions.
        htd: the htd file dictionary used
        columns: column names used to create the DataFrame and CSV output.
     Returns:
        A DataFrame containing information written to the output csv file.
     Catches:
        ValueError: catches value error from walk_files() if encountering a path longer than MAX_NAME characters
    """
    df = pd.DataFrame(columns=columns)
    walk = walk_files(root, extensions)
    for file, filepath, json, timepoint, zStep in walk:

        #check if the image is valid before adding it to the excel file
        if file in valid:
            #TODO use this function when testing on a machine with omero installed in python
            #match = checkName(file)   

            match = checkName(file, htd)
            # if there is 1 wavelength and/or site, then set it to 1 because it will not be included in the filename
            if htd["sites"] == 1 and htd["wavelength"]["number"] == 1:
                plateName, well, = match.groups()
                site = "s1"
                wavelength = "w1"
            elif htd["sites"] == 1:
                plateName, well, wavelength = match.groups()
                site = "s1"
            elif htd["wavelength"]["number"] == 1:
                plateName, well, site = match.groups()
                wavelength = "w1"
            else:
                plateName, well, site, wavelength = match.groups()

            # seperate the directories in the path from the ending file
            dirpath = os.path.dirname(filepath)

            # remove the root part of the dirname
            dirpath = dirpath.replace(root, "", 1)

            # split dirpath into list of directories
            dirs = []
            while 1:
                head, tail = os.path.split(dirpath)
                dirs.insert(0, tail)
                dirpath = head
                if (head == "") or (head == os.path.sep): # head=="" is first level file, head==os.path.sep is second or greater level file
                    break

            dirs.append(file)

            # join directories with "_"
            new_filename = "_".join(dirs)

            # truncate file name if too long
            if len(new_filename) > MAX_NAME:
                new_filename = truncate_name(dirs)

            # add row to the DataFrame
            #TODO: find out image name and MMA File path
            row = pd.DataFrame([[well,new_filename,file,filepath,json,site,wavelength,zStep,timepoint]],columns=columns)
            df = df._append(row, ignore_index=True)
        
    df.sort_values(by="File Name", inplace=True)
    return df


# NOTE: : doesn't close file after writing
def write_excel(file, df, sheet_number=3, cell="A2"):
    """Write DataFrame to an existing excel file on a specific sheet starting at a specific cell.

     Args:
        file: string file name.
        df: DataFrame table to write.
        sheet_number: integer zero-indexed index number of the sheet to write on.
        cell: cell to write DataFrame to.
     Returns:
        None
     Raises:
    """
    wb = xw.Book(file)
    sheet = wb.sheets[sheet_number]

    # Clear cells starting from the specified cell to the end of the used range
    clearStart = sheet.range(cell).address
    usedRange = sheet.used_range

    # define the range to clear
    clearRange = sheet.range(clearStart,(usedRange.last_cell.row,usedRange.last_cell.column))
    clearRange.clear()


    sheet[cell].options(index=False, header=False).value = df
    wb.save(file)

def read_excel(file, dataset_sheet=2, image_list_sheet=2, dataset_cell="B9", image_list_cell="B10"):
    """Read an excel file and extract dataset folder name and image file extensions from specific cells.

     Args:
        file: excel file.
        dataset_sheet: integer zero-indexed index number of the sheet containing dataset_cell.
        image_list_sheet: integer zero-indexed index number of the sheet containing image_list_cell.
        dataset_cell: string cell id of cell containing name of dataset flder.
        image_list_cell: string cell id of cell containing list of image file extensions.
     Returns:
        A tuple of (string dataset folder name, list of string image file extensions).
     Raises:
    """
    wb = xw.Book(file)
    sheet = wb.sheets[dataset_sheet]
    cell = sheet[dataset_cell]
    dataset = cell.value.strip()
    sheet = wb.sheets[image_list_sheet]
    cell = sheet[image_list_cell]
    extensions = cell.value
    extensions = extensions.split(" ")
    return (dataset, extensions)

#with a given directory eg. dataset5\Timepoint_1\ZStep_1
#extract the timepoint and ZStep. Covers all possible folder structure outcomes (missing ZStep folder or Timepoint folder...)
def getTandZ(dirpath):
    timepoint = ""
    zStep = ""
    parts = dirpath.split("\\")
    if len(parts) == 1:
        timepoint = "TimePoint_1"
        zStep = "ZStep_1"
    elif len(parts) == 3:
        timepoint= parts[1]
        zStep = parts[2]
    elif len(parts) == 2:
        if parts[1].split("_")[0] == "ZStep":
            zStep = parts[1]
            timepoint = "TimePoint_1"
        elif parts[1].split("_")[0] == "TimePoint":
            timepoint = parts[1]
            zStep = "ZStep_1"
    #return just the number of the timepoint and zStep
    return timepoint.split("_")[1], zStep.split("_")[1]

# MAIN
def main():
    excel = "POST-PUB_YCHAROS_template_noMacros_v16_Oct08_JL_CS_SPW_.xlsm"

    dataset, extensions = read_excel(excel)

    #get htd file
    htd = getHtdFile(dataset)

    #using the htd file, get dictionary of valid and refused images. Retreive incomplete wells too
    validImages,rejectedImages = getImages(dataset,htd)
    incomplete = getIncompleteWells(htd, validImages)

    #TODO add error if there is something in rejectedImages or incomplete.
    if rejectedImages or incomplete:
        print("error")

    #get list of image names to be displayed on excel file
    validImageNames = getValidImageNames(validImages)

    df = create_DataFrame(dataset,validImageNames,extensions,htd)
    write_excel(excel,df)

if __name__ == "__main__":
    main()