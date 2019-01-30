#include <util.h>

#include "globals.h"
#include "tasks.h"
#include "lcd.h"

void handleEKGResponse(CommunicationsData* commsDataPtr) {
  SoftwareSerial* peripheralSerialPtr = commsDataPtr->peripheralSerialPtr;

  while (!peripheralSerialPtr->available());

  char ekgResponseBytes[sizeof(EKGResponse)];
  peripheralSerialPtr->readBytes(ekgResponseBytes, sizeof(EKGResponse));
  EKGResponse* res = (EKGResponse*) &ekgResponseBytes;

  int i;
  for (i = 0; i < EKG_N; i++) {
    commsDataPtr->EKGRawBufPtr[i] = res->EKGRawData[i];
  }
}

void handleResponse(CommunicationsData* commsDataPtr) {
  SoftwareSerial* peripheralSerialPtr = commsDataPtr->peripheralSerialPtr;

  // Read in the response
  char responseBytes[sizeof(Response)];
  peripheralSerialPtr->readBytes(responseBytes, sizeof(Response));
  Response* res = (Response*) &responseBytes;

  DEBUGLN(res->resultData);

  // If we get a response, store the resulting information
  switch (res->function) {
    case COMM_TEMPERATURE:
      *(commsDataPtr->temperatureRawBufPtr + tempBufferIndex) = res->resultData;
      tempNewMeasurement = 1;
      break;
    case COMM_PRESSURE:
      *(commsDataPtr->bloodPressRawBufPtr + pressureBufferIndex) = res->resultData;

      while (!peripheralSerialPtr->available());

      peripheralSerialPtr->readBytes(responseBytes, sizeof(Response));
      *(commsDataPtr->bloodPressRawBufPtr + pressureBufferIndex + BUF_LENGTH) = res->resultData;
      bpNewMeasurement = 1;
      break;
    case COMM_PULSE:
      *(commsDataPtr->pulseRateRawBufPtr + pulseBufferIndex) = res->resultData;
      pulseNewMeasurement = 1;
      break;
    case COMM_RESP:
      *(commsDataPtr->respirationRateRawBufPtr + rrBufferIndex) = res->resultData;
      respirationNewMeasurement = 1;
      break;
    case COMM_EKG:
      // First response data is the sample frequency
      *(commsDataPtr->EKGSampleFreqPtr) = res->resultData;

      // Second, read in the massive 256-integer EKGResponse and save that
      handleEKGResponse(commsDataPtr);

      break;
    default:
      DEBUGLN("Invalid measurement selection");
      break;
  }
}

unsigned short write = 0;
unsigned short read = 0;

void communicationsTaskFunction(void* data) {
  CommunicationsData* commsDataPtr = (CommunicationsData*) data;

  unsigned short n = *commsDataPtr->measurementLengthPtr;

  if (read == n) { // implicitly, write == read == n
    read = 0;
    write = 0;

    // we are done with the comms task, why are we here?
    // copy
    tft.fillScreen(BLACK);

    // Add compute, warning/alarm, and display tasks
    addTask(computeTaskFunction, &computeData);
    addTask(warningAlarmTaskFunction, &warningAlarmData);
    addTask(displayTaskFunction, &displayData);

    // Add the EKG processing task
    int i;
    for (i = 0; i < n; i++) {
      if (commsDataPtr->measurementSelectionPtr[i] == COMM_EKG) {
        addTask(EKGProcessTaskFunction, &ekgProcessingData);
        break;
      }
    }

    // Delete self
    deleteCurrentTask = TRUE;
  } else if (write == read) {
    // writing step: create a message per measurement to be sent to the Uno
    Request req;
    req.function = commsDataPtr->measurementSelectionPtr[write];
    commsDataPtr->peripheralSerialPtr->write((char*) &req, sizeof(Request));

    write++;
  } else if (write == read + 1) {
    // reading step
    if (commsDataPtr->peripheralSerialPtr->available()) {
      handleResponse(commsDataPtr);

      read++;
    }
  } else {
    Serial.println("WE SHOULD NOT BE HERE EVER.");
  }

  return;
}
