#ifndef _GLOBALS_H
#define _GLOBALS_H

#include <defs.h>
#include <constants.h>

#include "scheduleList.h"
#include "tasks.h"

// Schedule list
extern ScheduleList scheduleList;
extern TCB* currentTask;
extern Bool deleteCurrentTask;

// buffer index for each measurement
extern unsigned int tempBufferIndex;
extern unsigned int pressureBufferIndex;
extern unsigned int pulseBufferIndex;
extern unsigned int rrBufferIndex;
extern unsigned int EKGFreqBufferIndex;

// warning count
extern unsigned int warningCount;

// alarms
extern unsigned char pulseWarningRange;
extern unsigned char tempWarningRange;
extern unsigned char bpWarningRange;
extern unsigned char bpAlarmRange;
extern unsigned char tempAlarmRange;
extern unsigned char pulseAlarmRange;
extern unsigned char respirationAlarmRange;
extern unsigned char EKGAlarmRange;
extern unsigned char battLow;

extern unsigned char tempAcknowledged;
extern unsigned char bpAcknowledged;
extern unsigned char pulseAcknowledged;
extern unsigned char respirationAcknowledged;

extern unsigned char pulseRateOn;
extern unsigned char tempOn;
extern unsigned char bpOn;

extern unsigned char freqNewMeasurement;
extern unsigned char periodNewMeasurement;
extern unsigned char timeIntNewMeasurement;
extern unsigned char spectrumNewMeasurement;
extern unsigned char eventNewMeasurement;


// remote variables
extern unsigned char displayEnabled;
extern unsigned char regularMeasurements;

// Data variables
extern ComputeData computeData;
extern DisplayData displayData;
extern WarningAlarmData warningAlarmData;
extern StatusData statusData;
extern TFTKeyPadData tftKeyPadData;
extern CommunicationsData communicationsData;
extern EKGProcessingData ekgProcessingData;
extern RemoteCommunicationsData remoteCommsData;
extern CommandData commandData;

#endif
