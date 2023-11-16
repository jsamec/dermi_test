from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import cv2
import numpy as np
import base64

from app.branje_kalibra_api import ImageProcessor

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
def test():
    return {"test": "test"}

#recive an image and return shape
@app.post("/process")
def predict(image: UploadFile = File(...)):
    #read image
    print("Got image")

    image = cv2.imdecode(np.fromstring(image.file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    #process image
    ip = ImageProcessor()
    ip.start(image)
    print(ip.EI)

    cv2.imwrite('test.jpg', ip.clear_skin)

    return_image = cv2.cvtColor(ip.clear_skin, cv2.COLOR_BGR2RGB)
    return_image = cv2.imencode('.jpg', return_image)[1].tobytes()
    return_image = base64.b64encode(return_image)

    ip.EI = round(ip.EI, 3)
    ip.corrected_median_pixel[0] = round(ip.corrected_median_pixel[0], 3)
    ip.corrected_median_pixel[1] = round(ip.corrected_median_pixel[1], 3)
    ip.corrected_median_pixel[2] = round(ip.corrected_median_pixel[2], 3)
    ip.corrected_median_pixel_CIELAB[0] = round(ip.corrected_median_pixel_CIELAB[0], 3)
    ip.corrected_median_pixel_CIELAB[1] = round(ip.corrected_median_pixel_CIELAB[1], 3)
    ip.corrected_median_pixel_CIELAB[2] = round(ip.corrected_median_pixel_CIELAB[2], 3)

    #return also clear_skin (cv2 image)
    return {'EI': ip.EI, 
            'returnImage': return_image, 
            'r': ip.corrected_median_pixel[0],
            'g': ip.corrected_median_pixel[1],
            'b': ip.corrected_median_pixel[2],
            'l': ip.corrected_median_pixel_CIELAB[0],
            'a': ip.corrected_median_pixel_CIELAB[1],
            'b2': ip.corrected_median_pixel_CIELAB[2],}



