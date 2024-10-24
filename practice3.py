import os
import json
import HTD_practice
from regexTest import getImages
import ezomero.json_api
import omero.clients
import ezomero
import omero.gateway
import omero.model
import omero.scripts as scripts
import omero
from omero.gateway import BlitzGateway
from omero.gateway import DatasetWrapper
from omero.gateway import ScreenWrapper
from omero.gateway import PlateWrapper
from omero.model import ScreenI
from omero.model import PlateI
from omero.model import WellI
from omero.model import ImageI
from omero.model import WellSampleI
from omero.model import ScreenPlateLinkI
from omero.rtypes import rint, rlong, rstring, robject, unwrap

# This is an updated version of practice 2 that only uploads validated images, 
# and uses siteId to upload multiple images per well


#Create a project with a database to store the images of a specific file, returns list of all images after uploading
def createProject(conn,directory,htd,projName,dataName):
    projId = ""
    dataId = ""
    
    #create a list of existing projects and datasets to prevent creating duplicates
    projects = []
    datasets = []
    for project in conn.getObjects("project"):
        projects.append(project.getName())
    for dataset in conn.getObjects("dataset"):
        datasets.append(dataset.getName())
    
    if projName not in projects:
        projId = ezomero.post_project(conn,projName)
    else:
        for proj in conn.getObjects("project", opts={'name': projName}):
            projId = proj.getId()

    if dataName not in datasets:
        dataId = ezomero.post_dataset(conn,dataName,projId)
    else:
        for data in conn.getObjects("dataset", opts={'name':dataName}):
            dataId = data.getId()

    return uploadImage(conn,directory,htd,projId, dataId)

# checks if an image is validated and does not exist before uploading it. Uploads image to specific dataset and project
def uploadImage(conn,directory,htd,projId,dataId):
    images = []
    #create a list of existing image names
    for image in conn.getObjects("image"):
        images.append(image.getName())

    #create a list of valid image names, store them in a dictionary so they can be easily referenced
    valid, refused = getImages(directory,htd)
    valid = dict(valid)
    validImages = []
    
    #get all the filenames that are valid
    for well in valid:
        for wavelength in valid[well]:
            for site in valid[well][wavelength]["Sites"]:
                validImages.append(valid[well][wavelength]["Sites"][site]["filename"])
    #if our valid image is not in the existing list of images, upload it
    for image in validImages:
        if image not in images:
            file_path = os.path.join(directory, image)
            ezomero.ezimport(conn,file_path,projId,dataId)
    return validImages

#create a plate for a specific screen
def createPlate(conn,name, screenId):
    plate = PlateWrapper(conn,PlateI())
    plate.setName(name)
    plate.save()
    plateId = plate.getId()

    #link the plate to the screen
    list = []
    list.append(plateId)
    ezomero.link_plates_to_screen(conn,list,screenId)

# This function converts wellId's to row-column format ex. E04 -> 5-4
def getWellCoords(input):
    col = int(input[1:])
    row = ord(input[0]) - ord('A') + 1
    #coord = str(row-1) + "-" + str(col-1)
    return row,col

def createWell(conn,plateId, row, col, imageId):
    well = WellI()
    well.setPlate(PlateI(plateId, False))
    well.setColumn(rint(col))
    well.setRow(rint(row))
    well.setPlate(PlateI(plateId, False))

    #Create Well Sample with Image
    createWellSample(conn,well,imageId)

# create a well sample with a given image
def createWellSample(conn,well,imageId):
    ws = WellSampleI()
    ws.setImage(ImageI(imageId,False))
    well.addWellSample(ws)
    update_service = conn.getUpdateService()
    update_service.saveObject(well)

#used to check if a site has been set already. returns true/false
def checkIfSiteIsSet(conn,siteId,plateId,row,col):
    plate = conn.getObject("plate",plateId)
    for well in plate.listChildren():
        if well.getRow() == row and well.getColumn() == col:
            wellSamples = well.listChildren()
            numSites = len(list(wellSamples))
            return numSites >= siteId
    return False


#either create a well if the site is 1, or add to it if it already exists and the site > 1
#siteNum the site id
#image: the image to be used
# row, col: the row and column of a well
def createOrAddToWell(conn,siteNum,plateId,imageId,row,col):
    if siteNum == 1:
        createWell(conn,plateId,row,col,imageId)
    else:
        #find the id of our selected well
        wellId = ""
        plate = conn.getObject("plate",plateId)
        wells = plate.listChildren()
        for well in wells:
            if well.getRow() == row and well.getColumn() == col:
                wellId = well.getId()
                wellWrapper = conn.getObject("well",wellId, opts={"load_images": True})
                well = wellWrapper._obj

                createWellSample(conn,well,imageId)

# creates a screen and plate for our images if they have not been created yet. returns the current screen Id
def createScreenAndPlate(conn,directory):
    #create a list of plate names
    plateNames = []
    screenId = ""
    screens = []
    for screen in conn.getObjects("screen", opts={'name':directory}):
        screens.append(screen.getName())
    if directory not in screens:
        screenId = ezomero.post_screen(conn, directory)
    else:
        for screen in conn.getObjects("screen", opts={'name': directory}):
                screenId = screen.getId()

    #Create a list of plate names
    for plate in conn.getObjects("plate",opts={'screen':screenId}):
        plateNames.append(plate.getName())

    return screenId,plateNames

# checks verifys if each image has been added to a site in a well. If not, then it adds the image
# siteCount: number of sites used in a well. images: the list of images being used
def addSitesToWells(conn,screenId,plateNames,siteCount,images):
    imageList = []
    #separate the images by _
    for image in images:
        x = image.split("_")
        imageList.append(x)

    #we will add the images in site 1 first, then site 2...
    for i in range(1,siteCount+1):
        for image in imageList:
            if int(image[2][1:]) == i:
                #if the plate has not been created yet on OMERO, we must create it
                if image[0] not in plateNames:
                    createPlate(conn,image[0],screenId)
                    plateNames.append(image[0])

                #get current plate id
                plateId = ""
                for plate in conn.getObjects("plate",attributes={'name':image[0]},opts={'screen':screenId}):
                    plateId = plate.getId()

                #get current image id
                imageId = ""
                serverImages = conn.getObjects("Image", attributes={"name": image[0]+"_"+image[1]+"_"+image[2]+"_"+image[3]})
                for serverImage in serverImages:
                    imageId = serverImage.getId()

                #get well coords
                row,col = getWellCoords(image[1])

                #if the site doesnt exist already,create or add to well
                if not checkIfSiteIsSet(conn,i,plateId,row-1,col-1):
                    createOrAddToWell(conn,i,plateId,imageId,row-1,col-1)


def main():
    #the file containing the images
    directory = "/root/omero/IF"

    # a list to hold all plate names
    plateNames = []

    # set the HTD file that is being used in this project

    htd = HTD_practice.getHtdFile(directory)

    conn =  BlitzGateway("root","omero_root_p4ss", host="192.168.56.56", port="4064", secure=True)
    conn.connect()

    images = createProject(conn,directory,htd,"Testing Project","Testing Database")

    screenId,plateNames = createScreenAndPlate(conn,directory)

    addSitesToWells(conn,screenId,plateNames,int(htd['sites']),images)

            
    conn.close()

if __name__ == "__main__":
    main()