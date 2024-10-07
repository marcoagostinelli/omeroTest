import omero
import ezomero
from imageio.v2 import imread

conn = ezomero.connect("root","omero_root_p4ss", host="192.168.56.56", port="4064", secure=True)

#def createMultiChannelImage(conn,)

#planes stores the arrays of pixels
im1 = imread("Plate35Plcg2_C05_s7_w1.TIF")
im2 = imread("Plate35Plcg2_C05_s7_w2.TIF")
im3 = imread("Plate35Plcg2_C05_s7_w3.TIF")
im4 = imread("Plate35Plcg2_C05_s7_w4.TIF")
planes = [im2,im4,im1,im3]

#imag1 used to retreive sizeX, sizeY, sizeZ
image1 = ""
for i in conn.getObjects("image",attributes={'name':"Plate35Plcg2_C05_s7_w1.TIF"}):
    image1 = i
 
# plane = image1.getPrimaryPixels().getPlane(0, 0, 0) 
# print(plane)

#TODO: figure out how zStep works
z=image1.getSizeZ()

#c is the number of images used 
c=len(planes)

#TODO: figure out how timepoint works
t=1
sizeX = image1.getSizeX()
sizeY = image1.getSizeY()



def planeGen():
    for p in planes:
        yield p

conn.createImageFromNumpySeq(
    planeGen(),"numpy image c05_S7", z,c,t
)


conn.close()