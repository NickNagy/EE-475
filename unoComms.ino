#include <SoftwareSerial.h>

SoftwareSerial mySerial(0, 1); // RX, TX

char counter = 0;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }


  //Serial.println("xx");

  // set the data rate for the SoftwareSerial port
  mySerial.begin(9600);
  //mySerial.println("Hello, world?");
}

void loop() { // run over and over
  mySerial.write(counter);
  if (mySerial.available()) {
    Serial.println(mySerial.read());
  }
  counter = (counter + 1) % 256;
}
