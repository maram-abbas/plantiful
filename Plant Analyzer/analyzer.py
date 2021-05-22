import cv2 as cv
import os
from color import classify
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
import boto3
import psycopg2
import datetime
import calendar
import time
import pickle
from segmenter import segment

conn = None
count = 5
s3 = None
bucket='cloud-cube-us2'

# connect to cloud cube AWS S3 storage bucket
def connectToStorage():
    global s3
    session = boto3.Session(
        aws_access_key_id='AKIA37SVVXBHX2CN4B6F',
        aws_secret_access_key='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',
    )
    s3 = session.resource('s3')

# connect to POSTGRESQL DB
def connectToDB ():
    global count
    global conn
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(
        host="ec2-52-204-141-94.compute-1.amazonaws.com",
        database="d2bdrrb43ij9sh",
        port="5432",
        user="espjozgwambwck",
        password="d298b438facae4eb774a9b0cba88a9f386034def5ff253771755f37b75488843")
    
    if conn is None and count > 0:
        print("Connection failed... trying again for the " + (count -  4) + " time.")
        count = count - 1
        connectToDB()
    elif count != 0:
        print("Connection successful.")
        count = 5
        return True
    else:
        print("Connection failed.")
        return False

# get all images where is_processed = 1
# return array of image paths in storage 
def getImages():
   
    global conn
    if conn is not None:
        print("Connection successful.")
       
        # create a cursor
        cur = conn.cursor()
        cur.execute('SELECT * FROM public.image WHERE is_processed = false')
        conn.commit()
        records = cur.fetchall()
        return records
    else:
        if (not connectToDB()):
            print("Connection failed.")
            return False

# open image from cloud storage (save it locally)
def openImage(filename):
    global s3
    # Filename - File to download
    # Bucket - Bucket to upload to (the top level directory under AWS S3)
    # Key - S3 object name (can contain subdirectories). If not specified then file_name is used
    print(filename)
    image_name=filename.split('/')
    s3.meta.client.download_file(Key=filename, Bucket=bucket,Filename=image_name[3])
    return image_name[3]

# growth stage model
def detectGrowthStage(filename):

    predictionn=''

    print("Loading classifier....")
    cascade_limestone = cv.CascadeClassifier('cascade/cascade.xml')

    df=pd.read_csv('training_data.csv') 

    lr = LogisticRegression(C=100)
    lr.fit(X=df[['Green Area','Yellow Area','No. of Green Contours','No. of Yellow Contours','No. of flowers']], y = df['Class'])

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([30, 255, 255])
    sensitivity = 20;
    lower_green=np.array([60 - sensitivity, 100, 50])
    upper_green=np.array([60 + sensitivity, 255, 255])

    image = cv.imread(filename)
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)

    rectangles = cascade_limestone.detectMultiScale(image)
    if(len(rectangles)>8):
        predictionn='Fruiting'
    else:
        prediction=classify(lr,hsv,lower_yellow,upper_yellow,lower_green,upper_green).split('\n')
        predictionn=prediction[0]
    
    return predictionn

# process image by changing is_processed=1
def process(id):
    global conn
    if conn is not None:
        print("Connection successful.")
        # create a cursor
        cur = conn.cursor()
        cur.execute('UPDATE public.image SET is_processed=true WHERE id = '+str(id))
        conn.commit()
        return True
    else:
        if (not connectToDB()):
            print("Connection failed.")
            return False

def detectSegmentHealth(filename):
    print(filename)
    # Load the model from disk
    model = pickle.load(open('svm_model.sav', 'rb'))

    # Read the test image
    img = cv.imread(filename)
    
    # Resize, flatten, and normalize the test image
    im_size = 150
    img = cv.resize(img, (im_size, im_size))
    image = np.array(img)
    image = image.flatten()
    image = image.astype('float32') / 255.0
    image = image.reshape(1, im_size**2*3)

    # Predict the image's health
    result = model.predict(image)
    if(result==[1.]):
        result="Unhealthy"
    elif(result==[0.]):
        result="Healthy"
    else:
        result="Undetermined"
    return result


def detectPlantHealth(filename):
    # Get number of leaf segments in image
    no_of_leaves=segment(filename)
    fn=filename.split('.')
    flag=0
    
    # Form path and detect path of each segment
    for i in range(no_of_leaves):
        print("in for loop for segments")
        path=fn[0]+'_'+str(i+1)+".jpg"
        # If at least one leaf is unhealthy -> plant is unhealthy
        if(detectSegmentHealth(path)=="Unhealthy"): 
            flag=1
        os.remove(path)
    
    # If no leaves are unhealthy, return healthy   
    if(flag==1):
        return "Unhealthy"
    else:
        return "Healthy"    

# WRITES PREDICTION INTO THE DATABASE
def writePrediction(img, growth_prediction,health_prediction):
    global conn
    if conn is not None:
        # create a cursor
        cur = conn.cursor()
        query="INSERT INTO public.prediction(group_id, growth_stage, created_at, image_path, health) VALUES ("+str(img[2])+", '"+growth_prediction+"',now(),'"+img[1]+"','"+health_prediction+"')"
        print(query)
        cur.execute(query)
        conn.commit()
        return True
    else:
        if (not connectToDB()):
            print("Connection failed.")
            return False

# main function for cron job 
def main():
    print("in main")
    connectToDB()
    connectToStorage()
    images=getImages()
    print("got images.....")
    if(images!=False):
        for i in images:
            print(i[1])
            img=openImage(i[1])
            growth_prediction=detectGrowthStage(img)
            health_prediction=detectPlantHealth(img)
            #write prediction into database 
            print(growth_prediction)
            print(health_prediction)
            writePrediction(i,growth_prediction,health_prediction)
            #change is_processed=true for i
            process(i[0])
            os.remove(img)
        print("Finished processing")
    else:
        print("No images to process")

            