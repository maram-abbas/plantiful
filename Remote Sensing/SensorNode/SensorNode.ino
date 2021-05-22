#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include "DHT.h"
#include <Preferences.h>

Preferences preferences;

#define DHTTYPE DHT11   // DHT 11

/*------------------------------------------------------------------------------------------*/

/*NETWORK AND WEB SERVER*/
// Network credentials
const char* ssid     = "SBAP-";
const char* password = "123456789";

AsyncWebServer server(80);

//Sensor Block MAC ADDRESS
String sensorBlockMacAddress;

//Wifi Network to connect to
const char* networkName = "null";
const char* networkPwd = "null";

const char* networkNameTemp = "null";
const char* networkPwdTemp = "null";

//SendData?
int senddata = 0;

//Intervals
int intervalHours = 0;
int intervalMinutes = 0;
int intervalSeconds = 0;
int totalIntervalInMs = 0;

/*------------------------------------------------------------------------------------------*/

/*SENSORS PART*/
// DHT Sensor
uint8_t DHTPin = 4; 
               
// Initialize DHT sensor.
DHT dht(DHTPin, DHTTYPE);                

float Temperature;
float Humidity;

//Soil Moisture Sensor
uint8_t soilPin = 36;
float soilMoisture;

//pH Sensor
float pH;
uint8_t pHPin = 35; 
int buf[10],temp;

/*------------------------------------------------------------------------------------------*/

/*CONNECTION TO RPI*/
const uint16_t port = 8090;
const char * host = "192.168.1.29";
String dataSent = "";

WiFiClient client;

//variable to store HTML
String ptr = "<!DOCTYPE html><html>\n";

void setup() {
      /*NETWORK AND WEB SERVER*/
      ptr +="<head><meta name=viewport content=width=device-width, initial-scale=1>\n";
      ptr +="<style type=\"text/css\" rel=\"stylesheet\">html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center} \n";
      ptr +=".button { background-color: #809fff; border: none; color: white; padding: 5px 10px; text-decoration: none; font-size: 20px; margin: 2px; cursor: pointer;}\n";
      ptr +="</style>\n";
      ptr +="</head>\n";
      ptr +="<body><h1>Sensor Block Configuration</h1>\n";
      ptr +="<form action=\"/get\">\n";
      ptr +="<br><br>\n";
      ptr +="<label for=\"ssids\">WiFi Name:</label>\n";
      ptr +="<select name=\"ssids\" id=\"ssids\">\n";

      int n = WiFi.scanNetworks();
      for (int i = 0; i < n; ++i)
      {
        ptr += "<option value=\"" + WiFi.SSID(i) + "\">" + WiFi.SSID(i) + "</option>\n";
      }
      
      ptr +="</select>\n";
      ptr +="<br><br>\n";
      ptr +="<label for=\"pwd\">WiFi Password:</label>\n";
      ptr +="<input type=\"text\" id=\"pwd\" name=\"pwd\">\n";
      ptr +="<br><br>\n";
      ptr +="<p><a href=/get><button class=button type=\"submit\" value=\"Submit\">OK</button></a></p>\n";
      ptr +="</form>\n";
      ptr +="<br><br>\n";
      ptr +="<form action=\"/get\">\n";
      ptr +="<p>Interval Time</p>\n";
      ptr +="<br>\n";
      ptr +="<label for=\"hours\">Hours</label>\n";
      ptr +="<input type=\"number\" id=\"hours\" name=\"hours\" min=\"0\" value=\"0\" oninput=\"validity.valid||(value='');\">\n";
      ptr +="<br>\n";
      ptr +="<label for=\"minutes\">Minutes</label>\n";
      ptr +="<input type=\"number\" id=\"minutes\" name=\"minutes\" min=\"0\" value=\"0\" oninput=\"validity.valid||(value='');\">\n";
      ptr +="<br>\n";
      ptr +="<label for=\"seconds\">Seconds</label>\n";
      ptr +="<input type=\"number\" id=\"seconds\" name=\"seconds\" min=\"0\" value=\"0\" oninput=\"validity.valid||(value='');\">\n";
      ptr +="<br><br>\n";
      ptr +="<p>Send Data?</p>\n";
      ptr +="<input type=\"radio\" id=\"yes\" name=\"senddata\" value=\"yes\">\n";
      ptr +="<label for=\"yes\">Yes</label>\n";
      ptr +="<br>\n";
      ptr +="<input type=\"radio\" id=\"no\" name=\"senddata\" value=\"no\" checked>\n";
      ptr +="<label for=\"no\">No</label>\n";
      ptr +="<br><br>\n";
      ptr +="<p><a href=/get><button class=button type=\"submit\" value=\"Submit\">OK</button></a></p>\n";
      ptr +="</form>\n";
      ptr +="</body></html>\n";

      Serial.begin(115200);

      //preferences retrieves previously stored variables --- if exists
      preferences.begin("my-app", false);

      networkName = preferences.getString("networkName", "null").c_str();
      networkPwd = preferences.getString("networkPwd", "null").c_str();
      senddata = preferences.getInt("senddata", 0);
      intervalHours = preferences.getInt("intervalHours", 0);
      intervalMinutes = preferences.getInt("intervalMinutes", 0);
      intervalSeconds = preferences.getInt("intervalSeconds", 0);
      Serial.println("Values from preferences:");
      Serial.println(networkName);
      Serial.println(networkPwd);
      Serial.println(intervalHours);
      Serial.println(intervalMinutes);
      Serial.println(intervalSeconds);

      //retrieving ESP32 Mac Address
      sensorBlockMacAddress = WiFi.macAddress();

      //try to reconnect to previously connected  network
      WiFi.reconnect();
    
      delay(7000);

      // if reconneection failed --- not in the same network anymore
      if (WiFi.status() != WL_CONNECTED) {

        Serial.println("WiFi NOT connected....  AP NOW");
        
        Serial.print("Setting AP (Access Point)…");
        
        String APnameTemp = ssid + sensorBlockMacAddress;
        const char* APname = APnameTemp.c_str();
        WiFi.softAP(APname);
      
        IPAddress IP = WiFi.softAPIP();
        Serial.print("AP IP address: ");
        Serial.println(IP);
      }
      else //wifi connection  established 
      {
        Serial.println("WiFi connected");
        Serial.println("IP address: ");
        Serial.println(WiFi.localIP());
      }

      //web server on "/" requests the configuration page
      server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send(200, "text/html", ptr.c_str());
      });

      //handling get request 
      server.on("/get", HTTP_GET, [] (AsyncWebServerRequest *request) {
        int paramsNr = request->params();

        int networkNameAdded = 0;
        int networkPwdAdded = 0;

        //looping on  the number of parameters found
        for(int i=0;i<paramsNr;i++)
      {
        AsyncWebParameter* p = request->getParam(i);
        Serial.print(p->value());
        
        //checking on the value of each parameter found
        if(p->value() == "")
        {
          Serial.print("NO VALUE ENTRED");
          request->send(200, "text/html", "Error! Please enter correct values! <br><a href=\"/\">Return to Configuration Page</a>");
        }
        else if(p->name() == "ssids")
        {
          networkNameTemp = p->value().c_str();
          networkNameAdded = 1;
        }
        else if(p->name() == "pwd")
        {
          networkPwdTemp = p->value().c_str();
          networkPwdAdded = 1;
        }
        else if(p->name() == "hours")
        {
          intervalHours = p->value().toInt();
          preferences.putInt("intervalHours", intervalHours);
        }
        else if(p->name() == "minutes")
        {
          intervalMinutes = p->value().toInt();
          preferences.putInt("intervalMinutes", intervalMinutes);
        }
        else if(p->name() == "seconds")
        {
          intervalSeconds = p->value().toInt();
          preferences.putInt("intervalSeconds", intervalSeconds);
        }
        else if(p->name() == "senddata")
        {
          if(p->value() == "yes")
          {
            senddata = 1;
          }
          else
          {
            senddata = 0;
          }
          preferences.putInt("senddata", senddata);
        }
      }

      //changing to the new wifi network that the user chose
      if(networkNameAdded == 1)
      {
        if(networkPwdAdded == 1)
        {
            WiFi.mode(WIFI_STA);
            WiFi.disconnect();
            delay(100);
            WiFi.begin(networkNameTemp, networkPwdTemp);

            delay(3000);
            
            if (WiFi.status() != WL_CONNECTED) 
            {
              Serial.println("WiFi NOT connected....  AP AGAIN");
              String APnameTemp = ssid + sensorBlockMacAddress;
              const char* APname = APnameTemp.c_str();
              WiFi.softAP(APname);
            }
            else
            {
              Serial.println("WiFi connected");
              Serial.println("IP address: ");
              Serial.println(WiFi.localIP());
              
              networkName = networkNameTemp;
              networkPwd =  networkPwdTemp;
              preferences.putString("networkName", networkName);
              preferences.putString("networkPwd", networkPwd);
            }

            networkNameAdded = 0;
            networkPwdAdded = 0;
        }
      } 
      });

        //starting the server
        server.begin();

        /*------------------------------------------------------------------------------------------*/
  
        /*SENSORS PART*/
        //DHT SENSOR
        pinMode(DHTPin, INPUT);
        dht.begin();
}

void loop() {

      Serial.println("Values from preferences:");
      Serial.println(networkName);
      Serial.println(networkPwd);
      Serial.println(intervalHours);
      Serial.println(intervalMinutes);
      Serial.println(intervalSeconds);

      //calculating the interval between readings in ms
      totalIntervalInMs = intervalHours * 60 * 60 * 1000;
      totalIntervalInMs += intervalMinutes * 60 * 1000;
      totalIntervalInMs += intervalSeconds * 1000;

      //if the user chose to send data to the Raspberry Pi
      if(senddata == 1)
      {
          Serial.println("send data = 1 and interval starting...wait");
          Serial.println(totalIntervalInMs);

          //ESP32 is set to be in low power mode while waiting for the interval to finish
          esp_sleep_enable_timer_wakeup(totalIntervalInMs);
          Serial.println("Setup ESP32 to sleep for every " + String(totalIntervalInMs) +
          " Milliseconds");
          esp_light_sleep_start();
          
          //connecting to the Raspberry Pi
          if (!client.connect(host, port)) //if connection failed
          {
             Serial.println("Connection to host failed! will try again next time.");
          }
          else //if connection succeeded
          {
              //DHT SENSOR
              Humidity = dht.readHumidity(); // Gets the value of the humidity
              Temperature = dht.readTemperature(); // Gets the value of the temperature
      
              //SOIL MOISTURE SENSOR
              soilMoisture = analogRead(soilPin);
              soilMoisture = map(soilMoisture,4070,1200,0,100);

              //pH SENSOR
              for(int i=0;i<10;i++) 
              { 
               buf[i]=analogRead(pHPin);
               Serial.println("buff");
               Serial.println(buf[i]);
               delay(10);
              }
              for(int i=0;i<9;i++)
              {
               for(int j=i+1;j<10;j++)
               {
                if(buf[i]>buf[j])
                {
                 temp=buf[i];
                 buf[i]=buf[j];
                 buf[j]=temp;
                }
               }
              }
              float avgValue=0;
              for(int i=2;i<8;i++)
                avgValue+=buf[i];
              avgValue/=5;
              avgValue/=1000;
              avgValue+=0.04;
              float pHVol =(float)avgValue/1024;
              pH = -5.70 * avgValue + 7;
              Serial.println("avg value");
              Serial.println(avgValue);
          
          
              //SEND DATA HERE
              dataSent += sensorBlockMacAddress;
              dataSent += ',';
              dataSent += String(Temperature,2);
              dataSent += ','; 
              dataSent += String(Humidity,2);
              dataSent += ',';
              dataSent +=  String(soilMoisture,2);
              dataSent += ',';
              dataSent +=  String(pH,2);
          
              client.print(dataSent);
              Serial.println(dataSent);
              Serial.println("data is sent!");
              
              dataSent = "";
              delay(100);
          }
      }
      else //user chose not to send data to Raspberry Pi
      {
        Serial.println("send data = 0 so nothing will be sent");
      }  

}


      
