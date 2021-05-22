
import numpy as np                                              # pip install numpy
import pandas as pd                                             # pip install pandas
import matplotlib.pyplot as plt                                 # pip install matplotlib
import os
import cv2                                                      # pip install opencv-python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
import pickle


# References: https://stackabuse.com/implementing-svm-and-kernel-svm-with-pythons-scikit-learn/
# STARTED AT 10:00 AM, 4/5/21


# Form path array
print("------------------------------INPUTS------------------------------")
#C:\Users\Admin-G06\Documents\PLANTIFUL\Mariam\Data\Ours
#C:\Users\Admin-G06\Documents\PLANTIFUL\Mariam\Data\KU Dataset (Edited)
#C:\Users\Admin-G06\Documents\PLANTIFUL\Mariam\Data\PlantVillage Dataset (Kaggle Edited)
#C:\Users\Admin-G06\Documents\PLANTIFUL\Mariam\Data\PlantVillage Dataset (TensorFlow Edited)

NUM = int(input('Enter how many sub-datasets you have. Each sub-dataset must have a folder called Healthy and another called Unhealthy.'))
print()

PATHS = []
for i in range(NUM):
    path = input("Enter path of sub-dataset %s." % str(i + 1))
    PATHS.append(path)
print()

print("------------------------------FOUND CLASSES------------------------------")
# Get names of classes
ARBIT_PATH = PATHS[0]
arbit_path = os.listdir(ARBIT_PATH)

CLASS_NAMES = os.listdir(ARBIT_PATH)
print("Number of classes: %d" % len(arbit_path))
print("The classes: %s" % CLASS_NAMES)
print()

print("------------------------------SUB-DATASET STATISTICS------------------------------")
for path in PATHS:
    dataset = os.path.basename(path)
    print("Size of sub-dataset %s:" % dataset)

    total = 0
    for class_name in CLASS_NAMES:
        class_images = os.listdir(path + '\\' + class_name)
        class_size =  len(class_images)
        total = total + class_size
        print("%s: %d " % (class_name, class_size))

    print("Total: %s" % total)
    print()

# Make images and labels arrays for each sub-dataset, tr-te divide them, then add them to tr and te (4 minutes)
train_x = np.empty(shape=(0, 150*150*3))
test_x = np.empty(shape=(0, 150*150*3))
train_y = np.empty(shape=(0, 1))
test_y = np.empty(shape=(0, 1))

for path in PATHS:
    im_size = 150
    images = np.empty(shape=(0, 150*150*3))
    Y = np.empty(shape=(0, 1))

    for class_name in CLASS_NAMES:
        class_path = path + '\\' + class_name
        class_images = [class_name for class_name in os.listdir(class_path)]

        # For each class
        for class_image in class_images:

            # Read, resize, flatten, and normalize each image
            img = cv2.imread(class_path + '\\' + class_image)
            img = cv2.resize(img, (im_size, im_size))
            image = np.array(img)
            image = image.flatten()
            image = image.astype('float32') / 255.0
            images = np.vstack((images, image))
            if class_name == 'Healthy':
                Y = np.vstack((Y, [0]))

            else:
                Y = np.vstack((Y, [1]))

    # Divide the images into training and testing
    images, Y = shuffle(images, Y, random_state=1)
    tr_x, te_x, tr_y, te_y = train_test_split(images, Y, test_size=0.2, random_state=415)
    train_x = np.vstack((train_x, tr_x))
    test_x = np.vstack((test_x, te_x))
    train_y = np.vstack((train_y, tr_y))
    test_y = np.vstack((test_y, te_y))


print("------------------------------TRAINING AND TESTING STATISTICS------------------------------")
print("Training input shape: ", train_x.shape)
print("Testing input shape: ", test_x.shape)
print("Training output shape: ", train_y.shape)
print("Testing output shape: ", test_y.shape)

# Create model with two classes
model = SVC(kernel='rbf')


print("------------------------------TRAINING------------------------------")
# Train the model (i.e. find weights optimal for the training images)

model.fit(train_x, train_y)
print()

print("------------------------------TESTING------------------------------")
# Test the model (i.e. find predictions for testing images)
pred_y = model.predict(test_x)
print(classification_report(test_y, pred_y))

# Save the model to disk
with open('C:/Users/Admin-G06/Documents/PLANTIFUL/Mariam/svm_model_82k.sav', 'wb') as f:
    pickle.dump(model, f)