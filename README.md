# plantiful :seedling: 	:ear_of_rice:


Welcome to the github repo of our senior project: an intelligent monitoring system for precision agriculture!

1. Documentation
    * You will find our report which details our implementation and testing of the system. You will also find the user guide which provides steps on how to set up and use the system. Finally, you will find the project’s Software Design Document (SDD) and Software Requirements Description (SRS).

1. Remote-Sensing
    * You will find the code for each microcontroller (ESP32) of a sensor node. The code reads from the sensors then sends the result to the project’s master microcontroller called Raspberry Pi. The code is already burned on the ESP32.

1. Remote-Capturing
    * You will find the code deployed on the Raspberry Pi. The code accesses the camera’s stream then uploads timed snapshots of the stream to the cloud.

1. Web Application
    * You will find the code for our web application. The application helps users see the system’s data and control the hardware. The application is Django-implemented. All the webpage frontend is in the sub-folder “templates”.

1. Plant Analyzer
    * You will find the codes for growth stage and health classification. 

1. Health Trainer 
    * You will find the trainers for our health model trials. Those are not deployed on the web application! Only their saved file and loader (called predictor) is. The trainers include an SVM and a CNN. The two trainers train and test a machine learning model to classify leaves as healthy or unhealthy.

1. Dagu, 
    * You will find the DAGU (car) code which is already loaded on the car’s microcontroller. The code makes the car perform infinite sequences of moving forward for a while then rotating.

1. Health Data Descriptions
    * You will find the descriptions of all datasets used in the health model with their links.




### Here are some useful links related to our project:
\
Our public repository:
https://github.com/maram-abbas/plantiful \
\
Our published growth stage and health dataset:
https://www.kaggle.com/farahseifeld/greenhouse-cucumber-growth-stages/metadata \
\
Web application homepage:
http://plantifulapptest.herokuapp.com/login/ \
\
Project final presentation:
https://www.youtube.com/watch?v=W78v6RIpsWc
