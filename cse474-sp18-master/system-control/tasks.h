#ifndef _TASKS_H
#define _TASKS_H

#include <SoftwareSerial.h>

// Data structs
typedef struct _ComputeData {
  unsigned int*     temperatureRawBufPtr;
  unsigned int*     bloodPressRawBufPtr;
  unsigned int*     pulseRateRawBufPtr;
  unsigned int*     respirationRateRawBufPtr;
  unsigned int*     EKGRawBufPtr;
  unsigned int*     EKGSampleFreqPtr;
  unsigned char**   tempCorrectedBufPtr;
  unsigned char**   bloodPressCorrectedBufPtr;
  unsigned char**   prCorrectedBufPtr;
  unsigned char**   respirationRateCorrectedBufPtr;
  unsigned char**   EKGFreqBufPtr;
  unsigned short*   measurementSelectionPtr;
  unsigned short*   measurementLengthPtr;
} ComputeData;

typedef struct _DisplayData {
  unsigned char**   tempCorrectedBufPtr;
  unsigned char**   bloodPressCorrectedBufPtr;
  unsigned char**   prCorrectedBufPtr;
  unsigned char**   respirationRateCorrectedBufPtr;
  unsigned char**   EKGFreqBufPtr;
  unsigned short*   batteryStatePtr;

  unsigned short* displayModePtr;
} DisplayData;

// NOTE: changed back to raw data instead of corrected data
typedef struct _WarningAlarmData {
  unsigned int*   temperatureRawBufPtr;
  unsigned int*   bloodPressRawBufPtr;
  unsigned int*   pulseRateRawBufPtr;
  unsigned int*   respirationRateRawBufPtr;
  unsigned int*   EKGRawBufPtr;
  unsigned short* batteryStatePtr;
} WarningAlarmData;

typedef struct _Status {
  unsigned short* batteryStatePtr;
} StatusData;

typedef struct _TFTKeyPadData {
  unsigned short* measurementSelectionPtr;
  unsigned short* measurementLengthPtr;
  unsigned short* displayModePtr;
} TFTKeyPadData;

typedef struct _CommunicationsData {
  unsigned short* measurementSelectionPtr;
  unsigned short* measurementLengthPtr;
  SoftwareSerial* peripheralSerialPtr;

  // NOTE replaced corrected with raw, because that's what the uno sends
  unsigned int* temperatureRawBufPtr;
  unsigned int* bloodPressRawBufPtr;
  unsigned int* pulseRateRawBufPtr;
  unsigned int* respirationRateRawBufPtr;
  unsigned int* EKGRawBufPtr;
  unsigned int* EKGSampleFreqPtr;
} CommunicationsData;

typedef struct _RemoteCommunicationsData {
  char*   remoteCommandPtr;
} RemoteCommunicationsData;

typedef struct _CommandData {
  char*           remoteCommandPtr;
  unsigned char** tempCorrectedBufPtr;
  unsigned char** bloodPressCorrectedBufPtr;
  unsigned char** prCorrectedBufPtr;
  unsigned char** respirationRateCorrectedBufPtr;
  unsigned char** EKGFreqBufPtr;
  unsigned short* batteryStatePtr;
  unsigned short* measurementSelectionPtr;
  unsigned short* measurementLengthPtr;
} CommandData;

// NOTE optional
typedef struct _TrafficManagementData {

} TrafficManagementData;

// NOTE im not convinced this is a necessary structure - Nick
typedef struct _EKGProcessingData {
  unsigned int* EKGRawBufPtr;
  unsigned int* EKGSampleFreqPtr;
  unsigned char** EKGFreqBufPtr;
} EKGProcessingData;

// Task functions
void schedulerTaskFunction(void);
void startupTaskFunction(void);
void computeTaskFunction(void*);
void displayTaskFunction(void*);
void warningAlarmTaskFunction(void*);
void statusTaskFunction(void*);
void communicationsTaskFunction(void*);
void tftKeyPadTaskFunction(void*);
void EKGProcessTaskFunction(void*);
void remoteCommunicationsTaskFunction(void*);
void commandTaskFunction(void*);

// Utility functions
void addTask(void (*taskFn)(void*), void* taskDataPtr);

#endif
