import cv2
import os
import time
import numpy as np
import time
import pandas as pd
import cv2
import numpy as np

def Attendence():

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read('trainer/trainer.yml')

    cascadePath = "haarcascade_frontalface_default.xml"

    faceCascade = cv2.CascadeClassifier(cascadePath)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cam = cv2.VideoCapture(0)
    df=pd.read_csv('StudentDetails.csv')
    ncount = []
    counts = 0
    while True:
            ret, im =cam.read()
            gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, 1.2,5)
            for(x,y,w,h) in faces:
                counts += 1
                cv2.rectangle(im, (x,y), (x+w,y+h), (0,255,0), 4)
                Id,i = recognizer.predict(gray[y:y+h,x:x+w])
                if i < 60:
                    name=df.loc[(df['Id']==Id)]['Name'].values[0]
                    cv2.putText(im, name, (x,y-40), font, 2, (255,255,255), 2)
                    if not name in ncount: 
                        ncount.append(name)
                else:
                    cv2.putText(im, "unknown", (x,y-40), font, 2, (255,255,255), 2)

            cv2.imshow('im',im)
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break
            elif counts > 26:
                break
    cam.release()
    cv2.destroyAllWindows()

    if len(ncount) > 0:
        return ncount
    else:
        return 'unknown'
