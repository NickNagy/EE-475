#include "globals.h"

// Schedule list
ScheduleList scheduleList;
TCB* currentTask;
Bool deleteCurrentTask;

// buffer index for each measurement
unsigned int tempBufferIndex;
unsigned int pressureBufferIndex;
unsigned int pulseBufferIndex;
unsigned int rrBufferIndex;
unsigned int EKGFreqBufferIndex;

// warning count
unsigned int warningCount;

// alarms
unsigned char pulseWarningRange;
unsigned char tempWarningRange;
unsigned char bpWarningRange;
unsigned char bpAlarmRange;
unsigned char tempAlarmRange;
unsigned char pulseAlarmRange;
unsigned char respirationAlarmRange;
unsigned char EKGAlarmRange;
unsigned char battLow;

unsigned char tempAcknowledged;
unsigned char bpAcknowledged;
unsigned char pulseAcknowledged;
unsigned char respirationAcknowledged;

// used for flashing warning
unsigned char pulseRateOn;
unsigned char tempOn;
unsigned char bpOn;

unsigned char freqNewMeasurement;
unsigned char periodNewMeasurement;
unsigned char spectrumNewMeasurement;
unsigned char timeIntNewMeasurement;
unsigned char eventNewMeasurement;



// remote variables
unsigned char displayEnabled;
unsigned char regularMeasurements;

// Data variables
CommandData commandData;
ComputeData computeData;
DisplayData displayData;
WarningAlarmData warningAlarmData;
StatusData statusData;
TFTKeyPadData tftKeyPadData;
CommunicationsData communicationsData;
EKGProcessingData ekgProcessingData;
RemoteCommunicationsData remoteCommsData;
