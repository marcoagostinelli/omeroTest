import os
import ezomero.json_api
import omero.clients
import ezomero
import omero.gateway
import omero.model
import omero.scripts as scripts
import omero
import re
import json
from omero.gateway import BlitzGateway
from omero.gateway import DatasetWrapper
from omero.gateway import ScreenWrapper
from omero.gateway import PlateWrapper
from omero.model import ScreenI, PlateI, WellI, ImageI, PixelsI, ChannelI
from omero.model import WellSampleI
from omero.model import ScreenPlateLinkI
from omero.model import LogicalChannelI
from omero.rtypes import rint, rlong, rstring, robject, unwrap, rdouble

from omero.gateway import BlitzGateway

conn = BlitzGateway("root","omero_root_p4ss", host="192.168.56.56", port="4064")
conn.connect()

image1 = conn.getObject("image",1004)
image2 = conn.getObject("image",1051)

def createMultiChannelImage(conn,images, datasetId, imageName):
    # Combines multiple images as different channels into one multi-channel image
    dataset = conn.getObject("dataset",datasetId)

    firstImage = images[0]
    sizeX = firstImage.getSizeX()
    sizeY = firstImage.getSizeY()
    sizeZ = firstImage.getSizeZ()
    sizeT = firstImage.getSizeT()
    sizeC = len(images)

    pixels = firstImage.getPixels(0)
    pixelsType = pixels.getPixelsType()

    # Get the PixelsService
    pixelsService = conn.getPixelsService()

    # Create the multi-channel image using positional arguments
    newImageId = pixelsService.createImage(
        sizeX,  # sizeX
        sizeY,  # sizeY
        sizeZ,  # sizeZ
        sizeT,  # sizeT
        #TODO fix this list
        [1] * sizeC,  # sizeC (number of channels)
        pixelsType,  # Pixel type (e.g., uint16)
        imageName,  # Image name
        "Multi-channel image created from existing images",  # Description
    )
    # Retrieve the newly created image object
    newImage = conn.getObject("Image", newImageId)

    # set each image as a channel (wavelength)
    for idx, image in enumerate(images):
        if idx < newImage.getSizeC():
            if image.getSizeC() > 0:
                emissionWave = image.getChannels()[0].getEmissionWave()# Get the emission wave from the original image
                
                # Create a new ChannelI object with the emission length
                logicalChannel = LogicalChannelI()
                logicalChannel.setEmissionWave(rdouble(emissionWave))

                # Create a new ChannelI object and associate the logical channel
                channel = ChannelI()
                channel.setLogicalChannel(logicalChannel)

                conn.getUpdateService().saveObject(channel)
    
    return newImage

multiChannelImage = createMultiChannelImage(conn, [image1, image2], 302, "test")
print(multiChannelImage)

conn.close()

