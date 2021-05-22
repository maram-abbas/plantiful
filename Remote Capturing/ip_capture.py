import cv2
import time
import os
from upload import uploadImage,connectToDB,getGroupId

def screenshot(i):
    global cap
    cv2.imwrite('plant'+str(i)+'.png',cap.read()[1]) # or saves it to disk
    return 'plant'+str(i)+'.png'

print("Before URL")



print("After URL")
i=0
timeout_start = time.time()
connectToDB()
print("begin timer")

start_time = time.time()
seconds = 50

# Captures image every 60 seconds
while True:
    # Camera IP Address is needed
    cap = cv2.VideoCapture('rtsp://admin:KGKSNI@192.168.1.172:554/H264?ch=1&subtype=0')

    current_time = time.time()
    elapsed_time = current_time - start_time

    if elapsed_time > seconds:
        print("Finished iterating in: " + str(int(elapsed_time))  + " seconds")
        print('About to start the Read command')
        ret, frame = cap.read()
        print('About to show frame of Video.')

        print('Running..')

        # Screenshoots stream and saves image
        img_name=screenshot(i)


        # Get group ID
        groupId = getGroupId("camera_1")
        
        # Uploads image to Cloud Storage and adds entry to db
        uploadImage(img_name,int(groupId))

        # Deletes locally stored image to save memory
        os.remove(img_name)

        i=i+1

        start_time = time.time()

cv2.destroyAllWindows()
