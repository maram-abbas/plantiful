import numpy as np
import cv2
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression

def getColoredContour(hsv,lower_color,upper_color):
        # Threshold the HSV image to get only the specified color
        mask_color = cv2.inRange(hsv, lower_color, upper_color)
        cnts = cv2.findContours(mask_color.copy(),
                                      cv2.RETR_EXTERNAL,
                                      cv2.CHAIN_APPROX_SIMPLE)[-2]
        cnts.sort(key=cv2.contourArea,reverse=True)
        return cnts

def findBestSen(hsv,min_sen, max_sen, min_dim, max_dim):
    found_cnts = []
    for sensitivity in range(min_sen, max_sen + 1):

        # Set color thresholds
        lower_green = np.array([60 - sensitivity, 100, 50])
        upper_green = np.array([60 + sensitivity, 255, 255])

        # Obtain green contours
        green_cnts = getColoredContour(hsv, lower_green, upper_green)
        green_cnts2 = green_cnts

        # Loop over all contours
        cnt_count = 0
        for cnt_index, cnt_area in enumerate(green_cnts2):
            # Find bounds of this contour
            (x, y, w, h) = cv2.boundingRect(cnt_area)

            # Add if large enough
            if (w >= min_dim and w <= max_dim) and (h >= min_dim and h <= max_dim):
                cnt_count = cnt_count+1

        # Count found contours for this sensitivity
        found_cnts.append(cnt_count)

    # Find sensitivity with max contours
    max_cnts = max(found_cnts)
    max_index = found_cnts.index(max_cnts)
    best_sen = min_sen + max_index

    return best_sen

 #filename should be without .jpg
def applySen(img,filename,best_sen, hsv, min_dim, max_dim):
    # Obtain color thresolds
    lower_green = np.array([60 - best_sen, 100, 50])
    upper_green = np.array([60 + best_sen, 255, 255])

    # Find contours
    greencnts = getColoredContour(hsv, lower_green, upper_green)
    valid = 0

    # Process the contours
    for cnt_area in greencnts:
        (x, y, w, h) = cv2.boundingRect(cnt_area)

        # Check if valid (medium-sized) contour
        if (w >= min_dim and w <= max_dim) and (h >= min_dim and h <= max_dim):
            valid = valid + 1
            num = str(valid)

            # Crop and save contour
            crop_img = img[y:y + h, x:x + w]
            crop_img = cv2.resize(crop_img, (150, 150))
           
            path = filename +'_'+ num+'.JPG'
            cv2.imwrite(path, crop_img)

            # Draw contour
            #cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)  # red rectangles with thickness 2
    return valid

# ------------------------------ MAIN ------------------------------
def segment(filename):
    # Process image
    im_size = 1000
    img = cv2.imread(filename)
    img = cv2.resize(img, (im_size, im_size))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Choose sensitivity with most valid (large) contours
    min_sen, max_sen, min_dim, max_dim = 10, 30, 55, 400
    best_sen = findBestSen(hsv,min_sen, max_sen, min_dim, max_dim)

    fn=filename.split('.')

    # Apply this sensitivity
    no_of_leaves = applySen(img,fn[0],best_sen, hsv, min_dim, max_dim)

    return no_of_leaves






