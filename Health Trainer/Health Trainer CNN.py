from __future__ import print_function
from keras.models import Model
from keras.layers import Flatten
from keras.layers import Dense
from keras.layers import Input
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import GlobalMaxPooling2D
from keras.layers import GlobalAveragePooling2D
from keras.preprocessing import image
from keras.utils import layer_utils
from keras.utils.data_utils import get_file
from keras import backend as K
from keras.applications.imagenet_utils import decode_predictions
from keras.applications.imagenet_utils import preprocess_input
#from keras.applications.imagenet_utils import _obtain_input_shape         # will work for Keras 2.2.0 or before
from keras.engine.topology import get_source_inputs
import numpy as np                                              # pip install numpy
import pandas as pd                                             # pip install pandas
import matplotlib.pyplot as plt                                 # pip install matplotlib
import os
import cv2                                                      # pip install opencv-python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split


# References: https://www.tensorflow.org/api_docs/python/tf/keras/Model
# STARTED AT 2:21 PM, 29/4/21

# Function to build a model with a VGG16 architecture with a custom image size
def VGGupdated(input_tensor=None, classes=2):
    # Image dimensions
    img_rows, img_cols = 150, 150  # was 256, 256; default size is 224,224
    img_channels = 3
    img_dim = (img_rows, img_cols, img_channels)

    img_input = Input(shape=img_dim)

    # --------------------------- Layers ---------------------------
    # (input to each layer is output to the previous one)

    # Block 1
    x = Conv2D(64, (3, 3), activation='relu', padding='same', name='block1_conv1')(img_input)
    x = Conv2D(64, (3, 3), activation='relu', padding='same', name='block1_conv2')(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='block1_pool')(x)

    # Block 2
    x = Conv2D(128, (3, 3), activation='relu', padding='same', name='block2_conv1')(x)
    x = Conv2D(128, (3, 3), activation='relu', padding='same', name='block2_conv2')(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='block2_pool')(x)

    # Block 3
    x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv1')(x)
    x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv2')(x)
    x = Conv2D(256, (3, 3), activation='relu', padding='same', name='block3_conv3')(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='block3_pool')(x)

    # Block 4
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv1')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv2')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block4_conv3')(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='block4_pool')(x)

    # Block 5
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv1')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv2')(x)
    x = Conv2D(512, (3, 3), activation='relu', padding='same', name='block5_conv3')(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='block5_pool')(x)

    # Classification block
    x = Flatten(name='flatten')(x)
    x = Dense(2024, activation='relu', name='fc1')(x)
    x = Dense(2024, activation='relu', name='fc2')(x)   # was 4096
    x = Dense(classes, activation='softmax', name='predictions')(x)

    # Create model with the image as the inputs and the class scores as the outputs
    model = Model(inputs=img_input, outputs=x, name='VGGdemo')

    return model

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
train_x = np.empty(shape=(0, 150, 150, 3))
test_x = np.empty(shape=(0, 150, 150, 3))
train_y = np.empty(shape=(0, 2))
test_y = np.empty(shape=(0, 2))

for path in PATHS:
    im_size = 150
    images = []
    Y = []

    for class_name in CLASS_NAMES:
        class_path = path + '\\' + class_name
        class_images = [class_name for class_name in os.listdir(class_path)]

        # For each class
        for class_image in class_images:
            img = cv2.imread(class_path + '\\' + class_image)
            img = cv2.resize(img, (im_size, im_size))
            images.append(img)
            if class_name == 'Healthy':
                Y.append([1, 0])

            else:
                Y.append([0, 1])

    # Normalize the images
    images = np.array(images)
    images = images.astype('float32') / 255.0

    Y = np.array(Y)

    # Divide the images into training and testing
    images, Y = shuffle(images, Y, random_state=1)
    tr_x, te_x, tr_y, te_y = train_test_split(images, Y, test_size=0.2, random_state=415)
    train_x = np.vstack((train_x, tr_x))
    test_x = np.vstack((test_x, te_x))
    train_y = np.vstack((train_y, tr_y))
    test_y = np.vstack((test_y, te_y))

    print()

print("------------------------------TRAINING AND TESTING STATISTICS------------------------------")
print("Training input shape: ", train_x.shape)
print("Testing input shape: ", test_x.shape)
print("Training output shape: ", train_y.shape)
print("Testing output shape: ", test_y.shape)

# Create model with two classes
model = VGGupdated(classes=2)

# Set parameters of the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("------------------------------TRAINING------------------------------")
# Train the model (i.e. find weights optimal for the training images)
# (10 epochs: 2.7 hr per epoch)

model.fit(train_x, train_y, epochs=10, batch_size=32)  # 32, 10
print()

print("------------------------------TESTING------------------------------")
# Test the model (i.e. find predictions for testing images)
# (takes 5 minutes)
preds = model.evaluate(test_x, test_y)
print("Loss = " + str(preds[0]))
print("Test accuracy = " + str(preds[1]))