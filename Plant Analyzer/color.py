import numpy as np
import cv2
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Get 3 largest areas in a contours array
def getArea(greencnts):
    cnt = 0;
    area=0
    a=0
    while cnt<3 and cnt<len(greencnts):
        green_area=greencnts[cnt]
        (xg,yg,wg,hg) = cv2.boundingRect(green_area)
        a=wg*hg
        area=area+a
        cnt=cnt+1
    return area

# Get colored contours area for specified color
def getColoredContour(hsv,lower_yellow,upper_yellow):
        # Threshold the HSV image to get only yellow colors
        mask_yellow = cv2.inRange (hsv, lower_yellow, upper_yellow)
        yellowcnts = cv2.findContours(mask_yellow.copy(),
                                      cv2.RETR_EXTERNAL,
                                      cv2.CHAIN_APPROX_SIMPLE)[-2]
        yellowcnts.sort(key=cv2.contourArea,reverse=True)
        return yellowcnts

# Get the number of flowers from a list of contours
def getNoValidFlowers(greencnts):
    cnt = 0
    a=0
    flower=0
    while cnt<len(greencnts):
        green_area=greencnts[cnt]
        (xg,yg,wg,hg) = cv2.boundingRect(green_area)
        a=wg*hg
        if(a<3000 and a>500):
            flower=flower+1
        cnt=cnt+1
    return flower

# step 2 of classification algorithm 
def classify(lr,hsv,lower_yellow,upper_yellow,lower_green,upper_green):
    
    # get feature vector
    yellowcnts=getColoredContour(hsv,lower_yellow,upper_yellow)
    greencnts=getColoredContour(hsv,lower_green,upper_green)
    green_area=getArea(greencnts)
    yellow_area=getArea(yellowcnts)
    flowers=getNoValidFlowers(yellowcnts)
   
    # Predict for new values using logistic regression model
    xvals = [[green_area,yellow_area,len(greencnts),len(yellowcnts),flowers]]
    x=np.array(xvals)
    predictions = lr.predict_proba(X=x)[:,1]
    
    probs = predictions
    
    if(probs>0.5):
        return "Flowering\n"
    else:
        return "Initial\n"
