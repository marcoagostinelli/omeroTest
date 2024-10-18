import os
import HTD_practice
import re
import json


#pattern = '(.+)_([A-Z]\d+)_(s\d+)_(w\d+)'

#This function returns a json that holds all possible wells/wavelengths/sites. Used for determining incomplet or missing wells
def getAllWells(htd):
    allWells = {}

    # number of sites in htd file
    siteCount = list(range(1,htd['sites']+1))
    # number of waves in htd file
    waveCount = htd['wavelength']['number']
    

    #populate the complete list of wells
    for well in htd['wells']:
        allWells[well] = {}
        for i in range(waveCount):
            allWells[well]["w"+str(i+1)] = {
                "Name": htd['wavelength']['names'][i],
                "Sites" : list(siteCount)
            }
    return allWells

#This is used to remove all used wells from the list of total wells, 
#leaving us with only the incomplete wells
def subtractJson(all,used):
    for well in used:
        #if the well is used, check if all wavelengths are there
        for wavelength in used[well]:
            
            #if the wavelength is used, check if all sites are there
            for site in used[well][wavelength]['Sites']:
                if (site in used[well][wavelength]['Sites']):
                    all[well][wavelength]['Sites'].remove(site)
                
                #if the wavelength is now empty, remove it
                if not all[well][wavelength]['Sites']:
                    del all[well][wavelength]
                
                #now, if the well is empty, remove it
                if not all[well]:
                    del all[well]
    return all

# checks if an image is in the correct format. Returns the image if true
def checkName(filename,htd):
    #if there are no sites, then the regex is
    if htd["sites"] == 1:
        regex = "(.+)_([A-Z]\d+)_(w\d+).TIF"
        return re.match(regex,filename)

    #if there are no waves, then the regex is
    if htd["wavelength"]["number"] == 1:
        regex = "(.+)_([A-Z]\d+)_(s\d+).TIF"
        re.match(regex,filename)
    
    if htd["sites"] == 1 and htd["wavelength"]["number"] == 1:
        regex = "(.+)_([A-Z]\d+).TIF"
        return re.match(regex,filename)

    #if there are both sites and waves, then the regex is
    regex = "(.+)_([A-Z]\d+)_(s\d+)_(w\d+).TIF"
    return re.match(regex,filename)
    




#matches every image in a folder to a regex and adds each part to the valid or refused JSON object
#htd: the htd dictionary that is being used
def getImages(directory,htd):

    validImages = {}
    refusedImages = {}

    for filename in os.listdir(directory):
        itemPath = os.path.join(directory, filename)
        # if its a directory, check if its a timepoint or zstep
        if os.path.isdir(itemPath):
            if filename.split("_")[0] == "TimePoint":
                timePoint = filename
                validImages[timePoint] = {}
                refusedImages[timePoint] = {}

                # we now search through the timepoint folder
                for timepointFileName in os.listdir(itemPath):
                    timepointFilePath = os.path.join(itemPath, timepointFileName)
                    if os.path.isdir(timepointFilePath):
                        if timepointFileName.split("_")[0] == 'ZStep':
                            ZStep = timepointFileName
                            validImages[timePoint][ZStep] = {}
                            refusedImages[timePoint][ZStep] = {}

                            # we now search through the zstep folder, it should only contain images
                            for zstepFileName in os.listdir(timepointFilePath):
                                validImages, refusedImages = readImage(directory,validImages, refusedImages,zstepFileName,timePoint,ZStep,htd)

                    #ZStep is 1 if there are no folders within a timepoint folder
                    else:

                        #if the ZStep_1 doesn't exist yet, create it
                        ZStep = "ZStep_1"
                        if ZStep not in validImages[timePoint]:
                            validImages[timePoint][ZStep] = {}
                            refusedImages[timePoint][ZStep] = {}
                        validImages, refusedImages = readImage(directory,validImages, refusedImages,timepointFileName,timePoint,ZStep,htd)


            #if there are no timepoint folders, then it must be a zstep folder
            elif filename.split("_")[0] == 'ZStep':
                ZStep = filename

                validImages[timePoint][ZStep] = {}
                refusedImages[timePoint][ZStep] = {}
                for zstepFileName in os.listdir(itemPath):
                    validImages, refusedImages = readImage(directory,validImages, refusedImages,zstepFileName,timePoint,ZStep,htd)  

        # if it is a file
        elif os.path.isfile(itemPath):
            timePoint = "TimePoint_1"
            ZStep = "ZStep_1"
            if timePoint not in validImages:
                validImages[timePoint] = {}
                refusedImages[timePoint] = {}
                validImages[timePoint][ZStep] = {}
                refusedImages[timePoint][ZStep] = {}
            
            validImages, refusedImages = readImage(directory,validImages, refusedImages,filename,timePoint,ZStep,htd)  
    return validImages, refusedImages

# sends an image to the valid or refused json object
#(valid or refused json objects must already be existing)
def readImage(directory,validImages, refusedImages,filename,timePoint,ZStep,htd):
     # verify the name matches the regex
    match = checkName(filename,htd)
    if match:
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
        
        # add the well if it doesn't exist in the valid json object
        if well not in validImages[timePoint][ZStep] and well in htd['wells']:
            validImages[timePoint][ZStep][well] = {}
        #add to refused images
        elif well not in refusedImages[timePoint][ZStep] and well not in htd['wells']:
            refusedImages[timePoint][ZStep][well] = {}


        #add the wavelength to the appropriate object if it has not been added yet
        if (well in validImages[timePoint][ZStep]):
            # add the wavelength if it does not exist and is valid
            if (wavelength not in validImages[timePoint][ZStep][well]) and (int(wavelength[1:]) <= htd['wavelength']['number']):
                validImages[timePoint][ZStep][well][wavelength] = {
                    "Name" : htd['wavelength']['names'][int(wavelength[1:]) -1],
                    "Sites" : {}
                }
        else:
            if (wavelength not in refusedImages[timePoint][ZStep][well]):
                refusedImages[timePoint][ZStep][well][wavelength] = {
                    #There is no name that exists for refused wells
                    "Sites": {}
                }
        #finally, add the site to the appropriate object if it has not been added yet
        if (int(site[1:]) <= htd['sites']) and (well in validImages[timePoint][ZStep]):
                if (int(site[1:]) not in validImages[timePoint][ZStep][well][wavelength]["Sites"]):
                    validImages[timePoint][ZStep][well][wavelength]["Sites"][int(site[1:])] = {
                        "filename": filename,
                        #TODO find out new filename
                        "newFilename": filename,
                        "filePath" : directory,
                        "Platename" : plateName,
                        "wellId" : well,
                        "siteId" : site,
                        "waveLengthId" : wavelength
                    }

        else:
            if (int(site[1:]) not in refusedImages[timePoint][ZStep][well][wavelength]["Sites"]):
                refusedImages[timePoint][ZStep][well][wavelength]["Sites"][int(site[1:])] = {
                    "filename": filename,
                    #TODO find out new filename
                    "newFilename" : filename,
                    "filePath" : directory,
                    "Platename" : plateName,
                    "wellId" : well,
                    "siteId" : site,
                    "waveLengthId" : wavelength
                }    
    return validImages, refusedImages  


#get all wells that are incomplete within a HTD object
# htd: the htd file dictionary
# validWells: the dictionary containing all valid wells
def getIncompleteWells(htd,validWells):
    allWells = getAllWells(htd)
    incompleteWells = subtractJson(allWells,validWells)
    return incompleteWells

#takes the valid image dictionary and returns a list containing every image name
def getValidImageNames(validImages):
    imageList = []
    for well in validImages:
        for wavelength in validImages[well]:
            for site in validImages[well][wavelength]["Sites"]:
                imageList.append(validImages[well][wavelength]["Sites"][site]["filename"])
    return imageList

            
def main():
    directory = '/root/omero/dataset3/'    
    # set the HTD file that is being used in this project
    htd = HTD_practice.getHtdFile(directory)


    validWells,invalidWells = getImages(directory,htd)

    incompleteWellsJson = open("incomplete.json", "w")
    validJson = open("valid.json", 'w')
    refusedJson = open("refused.json","w")

    json.dump(validWells, validJson, indent=4)
    json.dump(invalidWells, refusedJson, indent=4)

    #TODO add timepoint and zStep to incomplete json
    # #subtract valid wells from all wells to get incomplete wells
    # incompleteWells = getIncompleteWells(htd,validWells)
    # json.dump(incompleteWells,incompleteWellsJson, indent=4)

if __name__ == "__main__":
    main()