#include <SoftwareSerial.h>
#include <TimerOne.h>

#include <constants.h>
#include <util.h>

#include "measure.h"

// TODO this should be a TCB. We need the full-fledged schedule list here boi
MeasureData measureData;
EKGCaptureData ekgCaptureData;

unsigned int temperatureRaw;
unsigned int systolicPressRaw;
unsigned int diastolicPressRaw;
unsigned int pulseRateRaw;
unsigned int respirationRateRaw;

void initializeValues() {
  // raw data
  temperatureRaw = 75;
  systolicPressRaw = 110;
  diastolicPressRaw = 80;
  pulseRateRaw = 50;

  measureData.temperatureRawPtr = &temperatureRaw;
  measureData.systolicPressRawPtr = &systolicPressRaw;
  measureData.diastolicPressRawPtr = &diastolicPressRaw;
  measureData.pulseRateRawPtr = &pulseRateRaw;
  measureData.respirationRateRawPtr = &respirationRateRaw;
  // measureData.EKGRawPtr = &EKGRaw;

  ekgCaptureData.megaSerialPtr = &megaSerial;
}

void setup() {
  Serial.begin(9600);
  megaSerial.begin(9600);

  Serial.println("Hello world from peripheral");

  initializeValues();

  // Attaching interrupts for Pulse Rate, Blood Pressure button
  attachInterrupt(digitalPinToInterrupt(PULSE_PIN), pulseInterruptHandler, RISING);
  attachInterrupt(digitalPinToInterrupt(BP_BUTTON_PIN), bpButtonInterruptHandler, FALLING);
  Timer1.initialize(EKG_INTERVAL);
}

void handleSerial() {
  char requestBytes[sizeof(Request)];
  megaSerial.readBytes(requestBytes, sizeof(Request));
  Request* request = (Request*) &requestBytes;
  unsigned short measurement = request->function;

  Serial.print("Received request: ");
  Serial.println(measurement);

  // Build response to send back
  Response response;
  response.function = measurement;

  switch (measurement) {
    case COMM_TEMPERATURE:
      response.resultData = *measureData.temperatureRawPtr;
      megaSerial.write((char*) &response, sizeof(Response));
      return;
    case COMM_PRESSURE:
      // TODO two responses to respond with -- make it 1?
      response.resultData = *measureData.systolicPressRawPtr;
      megaSerial.write((char*) &response, sizeof(Response));

      response.resultData = *measureData.diastolicPressRawPtr;
      megaSerial.write((char*) &response, sizeof(Response));
      return;
    case COMM_PULSE:
      DEBUGLN(*measureData.pulseRateRawPtr);

      response.resultData = *measureData.pulseRateRawPtr;
      megaSerial.write((char*) &response, sizeof(Response));
      return;
    case COMM_RESP:
      response.resultData = *measureData.respirationRateRawPtr;
      megaSerial.write((char*) &response, sizeof(Response));
      return;
    case COMM_EKG:
      EKGCaptureTaskFunction(&ekgCaptureData);
      return;
    default:
      Serial.println("Unknown request");
      return;
  }
}

void loop() {
  measureTaskFunction(&measureData);

  if (megaSerial.available()) { // receive from mega
    handleSerial();
  }

  // TODO ?
  delay(100);
  return;
}
