import socket
import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading

#GLOBAL VARIABLES
conn = None
count = 5

def connectToDB ():
    global count
    global conn
    
    #CONNECTING TO DATABASE
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(
        host="ec2-52-204-141-94.compute-1.amazonaws.com",
        database="d2bdrrb43ij9sh",
        port="5432",
        user="espjozgwambwck",
        password="d298b438facae4eb774a9b0cba88a9f386034def5ff253771755f37b75488843")
    
    #RECONNECT IF CONNECTION FAILED
    if conn is None and count > 0: 
        print("Connection failed... trying again for the " + (count -  4) + " time.")
        count = count - 1
        connectToDB()
    elif count is not 0:
        print("Connection successful.")
        count = 5
        return True
    else:
        print("Connection failed.")
        return False


def addData (readings):
    global conn

    #readings contains the following format --- mac_address,temperature,humidity,moisture,pH
    #so we use a delimiter
    readings = readings.split(',')
    mac_address = readings[0]
    temp = readings[1]
    humidity = readings[2]
    moisture = readings[3]
    ph = readings[4]

    if conn is not None: #IF CONNECTION TO DATABASE IS SUCCESSFULL 
        print("Connection successful.")
        
        #CREATE A CURSOR
        cur = conn.cursor()
        
        #RETEIVING THE SENSOR BLOCK DATA FROM DATABASE
        cur.execute("SELECT * FROM public.sensor_block WHERE sensor_block_name = '" +  mac_address + "'")
        records = cur.fetchone()
        
        #ADDING NEW SENSOR READINGS TO DATABASE
        query = "INSERT INTO public.sensor_block_reading (sensor_block_id, temperature, humidity, moisture, ph, created_at) VALUES(" + str(records[0]) + ", " + str(temp) + ", " + str(humidity) + ", " + str(moisture) + ", " + str(ph) +", now());"
        print(query)
        cur.execute(query)
        conn.commit()
        
        cur.close()
        
        #CHECKS ON READINGS AND SEND NOTIFICATIONS IF READINGS ARE SUSPECIOUS
        sendNotification(mac_address, float(temp), float(humidity), float(moisture), float(ph))
        
        return True
    else:
        if (not connectToDB()):
            print("Connection failed.")
            return False


def sendNotification(sensor_block_name, temperature, humidity, moisture, ph):
    if conn is not None:
        
        #CREATE A CURSOR
        cur = conn.cursor()
        
        #RETEIVING THE SENSOR BLOCK DATA FROM DATABASE
        cur.execute("SELECT * FROM public.sensor_block WHERE sensor_block_name = '" +  str(sensor_block_name) + "'")
        record = cur.fetchone()
        groupId =  record[2];
        
        #RETEIVING THE SENSOR BLOCK GROUP FROM DATABASE
        cur.execute("SELECT * FROM public.grp WHERE id = '" +  str(groupId) + "'")
        record = cur.fetchone()
        settingsId =  record[2];
        projectId = record[1];
        
        #RETEIVING THE SENSOR BLOCK PROJECT FROM DATABASE
        cur.execute("SELECT * FROM public.project WHERE id = '" +  str(projectId) + "'")
        record = cur.fetchone()
        projectName =  record[1];
        
        #RETEIVING THE SENSOR BLOCK SETTINGS FROM DATABASE
        cur.execute("SELECT * FROM public.settings WHERE id = '" +  str(settingsId) + "'")
        record = cur.fetchone()
        min_temperature =  record[3];
        max_temperature = record[4];
        min_humidity = record[5];
        max_humidity = record[6];
        min_moisture = record[7];
        max_moisture = record[8];
        min_ph = record[9];
        max_ph = record[10];
        
        temperatureError = 0
        humidityError = 0
        moistureError = 0
        phError = 0
        
        #CHECKS IF READINGS ARE  IN RANGE
        if(temperature < min_temperature):
            temperatureError = 1
        elif(temperature > max_temperature):
            temperatureError = 1
            
        if(humidity < min_humidity):
            humidityError = 1
        elif(humidity > max_humidity):
            humidityError = 1
            
        if(moisture < min_moisture):
            moistureError = 1
        elif(moisture > max_moisture):
            moistureError = 1
            
        if(ph < min_ph):
            phError = 1
        elif(ph > max_ph):
            phError = 1
            
        
        #CREATING THE NOTIFICATION IF READINGS ARE OUT OF RANGE
        emailMessage = "Project Name: " + str(projectName) + "\n"
        emailMessage = emailMessage + "Group Number: " + str(groupId) + "\n"
        emailMessage = emailMessage + "Sensor Block Name: " + str(sensor_block_name) + "\n\n"
     
        
        if(temperatureError ==  1):
            print("send notification regarding temperature")
            emailMessage = emailMessage + "Temperature reading is out of range!\n"
            emailMessage = emailMessage + "Detected: " + str(temperature) + "°C\n"
            emailMessage = emailMessage + "Expected Temperature Range: " + str(min_temperature) + " - " + str(max_temperature) + "°C\n\n"
            
            
        if(humidityError ==  1):
            print("send notification regarding humidity")
            emailMessage = emailMessage + "Humidity reading is out of range!\n"
            emailMessage = emailMessage + "Detected: " + str(humidity) + "%\n"
            emailMessage = emailMessage + "Expected Humidity Range: " + str(min_humidity) + " - " + str(max_humidity) + "%\n\n"
            
            
        if(moistureError ==  1):
            print("send notification regarding moisture")
            emailMessage = emailMessage + "Moisture reading is out of range!\n"
            emailMessage = emailMessage + "Detected: " + str(moisture) + "%\n"
            emailMessage = emailMessage + "Expected Moisture Range: " + str(min_moisture) + " - " + str(max_moisture) + "%\n\n"
            
            
        if(phError ==  1):
            print("send notification regarding pH") 
            emailMessage = emailMessage + "pH reading is out of range!\n"
            emailMessage = emailMessage + "Detected: " + str(ph) + "\n"
            emailMessage = emailMessage + "Expected pH Range: " + str(min_ph) + " - " + str(max_ph) + "\n\n"
            
            
        #GET ALL USERS WORKING ON THE PROJECT OF THE CURRENT SENSOR NODE IN  ORDER TO NOTIFY THEM
        cur.execute("SELECT * FROM public.user_access WHERE project_id = '" +  str(projectId) + "'")
        records = cur.fetchall()
        
        for row in records:
            userId = row[1]
            cur.execute("SELECT * FROM public.usr WHERE id = '" +  str(userId) + "'")
            record = cur.fetchone()
            emailTo = record[1]
            firstNameTo = record[3]
            lastNameTo = record[4]
            
            sendEmail(emailTo, emailMessage, firstNameTo, lastNameTo)
            
            cur.execute("INSERT INTO public.notification (usr_id, project_id, group_id, msg, created_at) VALUES(" + str(userId) + ", " + str(projectId) + ", " + str(groupId) + ", '" + str(emailMessage) + "', now());")
            conn.commit()
       
  
        cur.close()

                
def sendEmail(emailTo, emailMessage, firstNameTo, lastNameTo):
    #SENDING NOTIFICATION EMAIL FROM PLANTIFUL'S ACCOUNT ON GOOGLE
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login("app.plantiful@gmail.com", "thesis_2020")

    msg = MIMEMultipart()       # create a message

    # setup the parameters of the message
    msg['From']="app.plantiful@gmail.com"
    msg['To']=emailTo
    msg['Subject']="Plantiful Notification"
    
    # add in the message body
    emailMessageFinal = "Hello " + firstNameTo + " " + lastNameTo + "!\n" +  emailMessage
    msg.attach(MIMEText(emailMessageFinal, 'plain'))
    
    # send the message via the server set up earlier.
    s.send_message(msg)
    
    
def newClient(client):
    #ALWAYS RECEIVE  READINGS FROM SENSOR NODES
    while True:
        
        content = client.recv(64)

        if len(content) == 0:
           break

        else:
            print(content)
            addData(content.decode("utf-8"))
    
    print("Closing connection")
    client.close()
    

'''
----------------------------------------------------------------------------MAIN HERE-----------------------------------------------------------------
'''

connectToDB()

s = socket.socket()         

s.bind(('0.0.0.0', 8090 ))
s.listen(0)  

while True:

    client, addr = s.accept()
    
    #EACH CLIENT IS HANDLED IN A NEW THREAD SO THAT BLOCKING DOES NOT HAPPEN
    x = threading.Thread(target=newClient, args=(client,))
    x.start()


s.close()