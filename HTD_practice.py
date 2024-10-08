import json

# This program will collect info from a HTD file

def parseContents(file):
    data = {}
    for line in file:
        line = line.strip()
        if line == '"EndFile"':
            break
        key, *value = line.split(', ')
        key = key.strip('"')

        # Handling boolean values
        value = [v.strip() == 'TRUE' for v in value] if any(v in ('TRUE', 'FALSE') for v in value) else [v.strip('"') for v in value]

        # Flatten lists if there's only one element
        if len(value) == 1:
            value = value[0]
        data[key] = value
    return data

# Read file contents of HTD and convert to JSON
def HTD_to_JSON(fileLocation):
    file = open(fileLocation, "r")
    parsedData = parseContents(file)

    # Convert the dictionary to JSON format
    jsonData = json.dumps(parsedData,indent=4)
    return json.loads(jsonData)

#returns a list of wavelength names
def getWaveLengthData(jsonFile):
    size = jsonFile.get("NWavelengths")

    # store the wavelength names in a list
    wavelengthNames = []

    # get the names of each wavelength
    for i in range(int(size)):
        wavelengthNames.append(jsonFile.get("WaveName"+str(i+1)))
    return wavelengthNames

#returns a list of the well names in use ex: A01, A03...
def getWells(jsonFile):
    wells = []

    #the column is the number
    xWells = jsonFile.get("XWells")

    #the row is the letter
    yWells = jsonFile.get("YWells")
    
    for i in range(int(yWells)):
        for j in range(int(xWells)):
            #check each well if it is used or not
            check = jsonFile.get("WellsSelection"+str(i+1))[j]
            if check is True:
                #get the corresponding letter for our number
                letter = chr(i + ord('A'))

                num = ""
                #make sure every number used is at least 2 digits. A1 -> A01
                if j < 10:
                    num = str(0) + str(j)
                else:
                    num = str(j)
                wells.append(letter+num)
    return wells

# Constructs a json file based on a given HTD file
# (This is the function we will be calling)
def constructHTDInfo(fileLocation):
    #writes HTD data to a json object for processing
    data = HTD_to_JSON(fileLocation)

    wellsList = getWells(data)
    waveList = getWaveLengthData(data)

    #create JSON object for output
    info = {}
    info['wavelength'] = {"number":len(waveList), "names":waveList}
    info['wells'] = wellsList
    #check if there are multiple sites
    if data.get("XSites"):
        info['sites'] = int(data.get("XSites")) * int(data.get("YSites"))
    else:
        info['sites'] = 1
    return info





