#if defined(ARDUINO) && (ARDUINO >= 100)
#include "Arduino.h"
#else
#include "WProgram.h"
#endif
#include <TimerOne.h>
#include <math.h>

#include <constants.h>
#include <util.h>

#include "measure.h"

SoftwareSerial megaSerial = SoftwareSerial(PERIPHERAL_RX, PERIPHERAL_TX);

// Pulse rate and respiratory rate variables
Bool firstPulseMeasurement = TRUE;
unsigned long lastPulseTime = 0;
volatile float pulseFrequency = 0;

// Private blood pressure variables
volatile unsigned int bpRaw = 80;
volatile int counter = 0;

////// EKG methods //////

#define USE_INTERRUPTS 0

unsigned long EKGStart;
unsigned long EKGFinish;

volatile unsigned int EKGRaw[EKG_N];
volatile unsigned int EKGRawIndex;

void doneMeasuringEKG() {
  EKGRawIndex = 0;

  // Send the sample frequency
  unsigned int EKGMeasuredSampleFreq = 1000000*EKG_N/(EKGFinish - EKGStart);

  Response response;
  response.function = COMM_EKG;
  response.resultData = (USE_INTERRUPTS ? EKG_SAMPLE_FREQ : EKGMeasuredSampleFreq);
  megaSerial.write((char*) &response, sizeof(Response));

  EKGResponse ekgResponse;
  int i;
  for (i = 0; i < EKG_N; i++) {
    ekgResponse.EKGRawData[i] = EKGRaw[i];
  }
  megaSerial.write((char*) &ekgResponse, sizeof(EKGResponse));
}

void ekgTimerInterruptHandler() {
  unsigned int val = analogRead(EKG_PIN);
  EKGRaw[EKGRawIndex++] = val;

  if (EKGRawIndex >= EKG_N) {
    Timer1.detachInterrupt();
    EKGFinish = micros();

    doneMeasuringEKG();
  }
}

////// End EKG methods //////

////// Interrupt handlers //////

void pulseInterruptHandler() {
  unsigned long currMillis = millis();

  if (firstPulseMeasurement) {
    firstPulseMeasurement = FALSE;
    lastPulseTime = currMillis;
    return;
  }

  // Compute frequency based on the time that has passed
  float period = ((float)(currMillis - lastPulseTime)) / 1000.0;
  // Range of valid frequency: 0.5 Hz to 50Hz reliable
  // Amplitude: 100 mV square wave
  pulseFrequency = 1.0 / period;
  lastPulseTime = currMillis;
}

void bpButtonInterruptHandler() {
  DEBUGLN("Hello from BP button!");

  // Increment/decrement the bpRaw
  int bpSwitchVal = digitalRead(BP_SWITCH_PIN);

  if (bpSwitchVal) {
    bpRaw = 1.1*bpRaw;
  } else {
    bpRaw = 0.9*bpRaw;
  }

  DEBUGLN(bpRaw);
}

////// Task functions //////

void measureTaskFunction(void* data) {
  // Cast the parameter to MeasureData
  MeasureData* measureDataPtr = (MeasureData*) data;

  unsigned int tempRaw        = *measureDataPtr->temperatureRawPtr;
  unsigned int spRaw          = *measureDataPtr->systolicPressRawPtr;
  unsigned int dpRaw          = *measureDataPtr->diastolicPressRawPtr;
  unsigned int prRaw          = *measureDataPtr->pulseRateRawPtr;
  unsigned int rrRaw          = *measureDataPtr->respirationRateRawPtr;

  // delta for correction
  float delta;

  // temperature
  unsigned int pinValue = analogRead(TEMP_PIN);
  unsigned int newTempRaw = map(pinValue, 0, 1023, TEMP_LOWER_LIM, TEMP_UPPER_LIM);
  // Only update if there's a >= 15% change
  delta = 0.15 * (50.0 - 25.0);
  if (abs(newTempRaw - tempRaw) > delta) {
    tempRaw = newTempRaw;
  }

  // blood pressure
  // systolic measurement if in systolic range, diastolic measurement if in diastolic range
  if (bpRaw >= SP_LOWER_LIM && bpRaw <= SP_UPPER_LIM) {
    spRaw = bpRaw;
  } else if (bpRaw >= DP_LOWER_LIM && bpRaw <= DP_UPPER_LIM) {
    dpRaw = bpRaw;
  }

  // pulse rate
  unsigned int newPrRaw = (unsigned int)(round(60.0 * pulseFrequency));
  delta = 0.15 * prRaw;
  if (abs(newPrRaw - prRaw) > delta) {
    prRaw = newPrRaw;
  }

  // respiration rate
  unsigned int newRrRaw = (unsigned int)(round(60.0 * pulseFrequency));
  delta = 0.15 * rrRaw;
  if (abs(newRrRaw - rrRaw) > delta) {
    rrRaw = newRrRaw;
  }

  // Save the information in the MeasureData object
  *measureDataPtr->temperatureRawPtr        = tempRaw;
  *measureDataPtr->systolicPressRawPtr      = spRaw;
  *measureDataPtr->diastolicPressRawPtr     = dpRaw;
  *measureDataPtr->pulseRateRawPtr          = prRaw;
  *measureDataPtr->respirationRateRawPtr    = rrRaw;
}

void EKGCaptureTaskFunction(void* data) {
  EKGCaptureData* EKGCaptureDataPtr = (EKGCaptureData*) data;

  if (USE_INTERRUPTS) {
    EKGRawIndex = 0;
    EKGStart = micros();
    Timer1.attachInterrupt(ekgTimerInterruptHandler);

    // TODO block all other incoming serial requests?
  } else {
    EKGStart = micros();
    unsigned int val;
    for (int i = 0; i < EKG_N; i++){
      val = analogRead(EKG_PIN);
      EKGRaw[i] = val;
    }
    EKGFinish = micros();
    doneMeasuringEKG();
  }
}
