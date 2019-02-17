#include <SoftwareSerial.h>
SoftwareSerial mySerial(19, 18); // TX & RX on Mega

bool whichMeasurement[3];

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
}

void loop() {
  if (mySerial.available()) {
    if(mySerial.read()){
      mySerial.readBytes(whichMeasurement, 5);
      // set up interrupt, measure
    }
  }
  if (Serial.available()) {
    mySerial.write(Serial.read());
  }
}

void makeMeasurement(){
  if (whichMeasurement[0]){
    
  }
  if (whichMeasurement[1]){
    
  }
}

