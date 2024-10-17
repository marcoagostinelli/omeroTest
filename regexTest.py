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
def checkName(filename):
    regex = "(.+)_([A-Z]\d+)_(s\d+)_(w\d+).TIF"
    return re.match(regex,filename)




#matches every image in a folder to a regex and adds each part to the valid or refused JSON object
#htd: the htd dictionary that is being used
def getImages(directory,htd):
    validImages = {}
    refusedImages = {}

    for filename in os.listdir(directory):
        # verify the name matches the regex
        match = checkName(filename)
        #(plateName_well_site_wavelength)
        if match:
            plateName, well, site, wavelength = match.groups()
            
            # add the well if it doesn't exist in the valid json object
            if well not in validImages and well in htd['wells']:
                validImages[well] = {}
            #add to refused images
            elif well not in refusedImages and well not in htd['wells']:
                refusedImages[well] = {}


            #add the wavelength to the appropriate object if it has not been added yet
            if (well in validImages):
                # add the wavelength if it does not exist and is valid
                if (wavelength not in validImages[well]) and (int(wavelength[1:]) <= htd['wavelength']['number']):
                    validImages[well][wavelength] = {
                        "Name" : htd['wavelength']['names'][int(wavelength[1:]) -1],
                        "Sites" : {}
                    }
            else:
                if (wavelength not in refusedImages[well]):
                    refusedImages[well][wavelength] = {
                        #There is no name that exists for refused wells
                        "Sites": {}
                    }
            #finally, add the site to the appropriate object if it has not been added yet
            if (int(site[1:]) <= htd['sites']) and (well in validImages):
                    if (int(site[1:]) not in validImages[well][wavelength]["Sites"]):
                        validImages[well][wavelength]["Sites"][int(site[1:])] = {
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
                if (int(site[1:]) not in refusedImages[well][wavelength]["Sites"]):
                    refusedImages[well][wavelength]["Sites"][int(site[1:])] = {
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
    directory = '/root/omero/IF/'    
    # set the HTD file that is being used in this project
    htd = HTD_practice.getHtdFile(directory)


    validWells,invalidWells = getImages(directory,htd)

    incompleteWellsJson = open("incomplete.json", "w")
    validJson = open("valid.json", 'w')
    refusedJson = open("refused.json","w")

    json.dump(validWells, validJson, indent=4)
    json.dump(invalidWells, refusedJson, indent=4)

    #subtract valid wells from all wells to get incomplete wells
    incompleteWells = getIncompleteWells(htd,validWells)
    json.dump(incompleteWells,incompleteWellsJson, indent=4)

if __name__ == "__main__":
    main()