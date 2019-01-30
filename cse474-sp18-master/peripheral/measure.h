#ifndef _TASKS_H
#define _TASKS_H

#include <SoftwareSerial.h>

#include <defs.h>
#include <constants.h>

// Pins for analog on peripheral
#define TEMP_PIN      A0
#define EKG_PIN       A1
#define BP_SWITCH_PIN 4
#define BP_BUTTON_PIN 3
#define PULSE_PIN     2
// NOTE: using the same pin because we only have one measurement at a time
#define RESP_PIN      PULSE_PIN

typedef struct _MeasureData {
  unsigned int*   temperatureRawPtr;
  unsigned int*   systolicPressRawPtr;
  unsigned int*   diastolicPressRawPtr;
  unsigned int*   pulseRateRawPtr;
  unsigned int*   respirationRateRawPtr;
  unsigned int*   EKGRawPtr;
  unsigned short* measurementSelectionPtr;
} MeasureData;

typedef struct _EKGCaptureData {
  SoftwareSerial* megaSerialPtr;
} EKGCaptureData;

void measureTaskFunction(void* data);
void EKGCaptureTaskFunction(void* data);

// Interrupt handlers
void pulseInterruptHandler();
void bpButtonInterruptHandler();

// Globals
extern SoftwareSerial megaSerial;

#endif _TASKS_H
