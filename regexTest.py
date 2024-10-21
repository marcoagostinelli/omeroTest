import os
import HTD_practice
import re
import json


#This function returns a json that holds all possible wells/wavelengths/sites. Used for determining incomplet or missing wells
def getAllWells(htd):
    allWells = {}
    # number of sites in htd file
    siteCount = list(range(1,htd['sites']+1))
    # number of waves in htd file
    waveCount = htd['wavelength']['number']

    for i in range(1,htd['TimePoints']+1):
        timepoint = "TimePoint_"+str(i)
        allWells[timepoint] = {}
        for j in range(1,htd['ZSteps']+1):
            zStep = "ZStep_"+str(j)
            allWells[timepoint][zStep] = {}

            #populate the complete list of wells
            for well in htd['wells']:
                allWells[timepoint][zStep][well] = {}
                for i in range(waveCount):
                    allWells[timepoint][zStep][well]["w"+str(i+1)] = {
                        "Name": htd['wavelength']['names'][i],
                        "Sites" : list(siteCount)
                    }

    return allWells

#This is used to remove all used wells from the list of total wells, 
#leaving us with only the incomplete wells
def subtractJson(all,used):
    for timepoint in used:
        for zStep in used[timepoint]:
            for well in used[timepoint][zStep]:
            #if the well is used, check if all wavelengths are there
                for wavelength in used[timepoint][zStep][well]:
                #if the wavelength is used, check if all sites are there
                    for site in used[timepoint][zStep][well][wavelength]['Sites']:
                        #remove site
                        if (site in used[timepoint][zStep][well][wavelength]['Sites']):
                            all[timepoint][zStep][well][wavelength]['Sites'].remove(site)

                        #if the wavelength is now empty, remove it
                        if not all[timepoint][zStep][well][wavelength]['Sites']:
                            del all[timepoint][zStep][well][wavelength]
                        
                        #if the well is now empty, remove it
                        if not all[timepoint][zStep][well]:
                            del all[timepoint][zStep][well]
                        
                        #if the zStep is now empty, remove it
                        if not all[timepoint][zStep]:
                            del all[timepoint][zStep]
                        
                        #if the timepoint is now empty, remove it
                        if not all[timepoint]:
                            del all[timepoint]
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
                        #find the zstep folder
                        #however, if the ZStep is 0, then we don't add it
                        #TODO process Zprojections
                        if timepointFileName.split("_")[0] == 'ZStep' and int(timepointFileName.split("_")[1]) != 0:
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
    
    #remove empty timepoints if any
    validImages = cleanEmptyEntries(validImages)
    refusedImages = cleanEmptyEntries(refusedImages)
        
    return validImages, refusedImages

def cleanEmptyEntries(refusedImages):
    # Collect timepoints and z-steps to delete
    timepointsToDelete = []

    for timePoint in list(refusedImages.keys()):
        zstepsToDelete = []

        # Collect empty ZSteps to delete within the current timepoint
        for ZStep in list(refusedImages[timePoint].keys()):
            if refusedImages[timePoint][ZStep] == {}:
                zstepsToDelete.append(ZStep)

        # Delete empty ZSteps after collecting them
        for ZStep in zstepsToDelete:
            del refusedImages[timePoint][ZStep]

        # If the entire timepoint is empty, mark it for deletion
        if refusedImages[timePoint] == {}:
            timepointsToDelete.append(timePoint)

    # Delete empty timepoints after collecting them
    for timePoint in timepointsToDelete:
        del refusedImages[timePoint]

    # Return the cleaned dictionary
    return refusedImages

# sends an image to the valid or refused json object
#(valid or refused json objects must already be existing)
#TODO: check for valid/invalid timepoint and zStep
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
    directory = '/root/omero/dataset4/'    
    # set the HTD file that is being used in this project
    htd = HTD_practice.getHtdFile(directory)


    validWells,invalidWells = getImages(directory,htd)

    incompleteWellsJson = open("incomplete.json", "w")
    validJson = open("valid.json", 'w')
    refusedJson = open("refused.json","w")

    json.dump(validWells, validJson, indent=4)
    json.dump(invalidWells, refusedJson, indent=4)

    #TODO add timepoint and zStep to incomplete json
    #subtract valid wells from all wells to get incomplete wells
    incompleteWells = getIncompleteWells(htd,validWells)
    json.dump(incompleteWells,incompleteWellsJson, indent=4)

if __name__ == "__main__":
    main()