#if defined(ARDUINO) && (ARDUINO >= 100)
#include "Arduino.h"
#else
#include "WProgram.h"
#endif
#include "HardwareSerial.h"
#include <ctype.h>

#include <defs.h> // for Bool
#include <util.h>

#include "tasks.h"
#include "globals.h"

Bool remoteInitialized = FALSE;

//// Private methods ////

// for printing most recent measurements to Serial
void printMeasured(CommandData* commandDataPtr) {
  Serial.println("Most recent measured values: ");
  // temperature
  Serial.print("\t Temperature: ");
  Serial.print((char*) commandDataPtr->tempCorrectedBufPtr[(tempBufferIndex-1)%BUF_LENGTH]);
  Serial.println(" degrees C");
  // systolic
  Serial.print("\t Systolic Pressure: ");
  Serial.print((char*) commandDataPtr->bloodPressCorrectedBufPtr[(pressureBufferIndex-1)%BUF_LENGTH]);
  Serial.println(" mm Hg");
  // diastolic
  Serial.print("\t Diastolic Pressure: ");
  Serial.print((char*) commandDataPtr->bloodPressCorrectedBufPtr[(pressureBufferIndex-1)%BUF_LENGTH+BUF_LENGTH]);
  Serial.println(" mm Hg");
  // pulse
  Serial.print("\t Pulse Rate: ");
  Serial.print((char*) commandDataPtr->prCorrectedBufPtr[(pulseBufferIndex-1)%BUF_LENGTH]);
  Serial.println(" BPM");
  // respiration
  Serial.print("\t Respiration Rate: ");
  Serial.print((char*) commandDataPtr->respirationRateCorrectedBufPtr[(rrBufferIndex-1)%BUF_LENGTH]);
  Serial.println(" breaths per minute");
  // EKG
  Serial.print("\t EKG: ");
  Serial.print((char*) commandDataPtr->EKGFreqBufPtr[(EKGFreqBufferIndex-1)%BUF_LENGTH]);
  Serial.println(" Hz");
  Serial.print("\t Battery: ");
  Serial.print(*commandDataPtr->batteryStatePtr);
  Serial.println("%");
  // TODO uncomment
  // Serial.print("\t Warnings: ");
  // Serial.println(warningCount);
}

void printWarnings() {
  Bool noWarnings = TRUE;

  // temperature
  if (tempWarningRange) {
    noWarnings = FALSE;
    if (tempAlarmRange) {
      Serial.println("ALERT! TEMPERATURE CRITICALLY OUT OF RANGE.");
    } else {
      Serial.println("WARNING: TEMPERATURE OUT OF RANGE.");
    }
  }
  // bp
  if (bpWarningRange) {
    noWarnings = FALSE;
    if (bpAlarmRange) {
      Serial.println("ALERT! BLOOD PRESSURE CRITICALLY OUT OF RANGE.");
    } else {
      Serial.println("WARNING: BLOOD PRESSURE OUT OF RANGE.");
    }
  }
  // pulse
  if (pulseWarningRange) {
    noWarnings = FALSE;
    if (pulseAlarmRange) {
      Serial.println("ALERT! PULSE RATE CRITICALLY OUT OF RANGE.");
    } else {
      Serial.println("WARNING: PULSE RATE OUT OF RANGE.");
    }
  }
  // respiration
  if (respirationAlarmRange) {
    noWarnings = FALSE;
    Serial.println("ALERT! RESPIRATION RATE CRITICALLY OUT OF RANGE.");
  }
  // EKG
  if (EKGAlarmRange) {
    noWarnings = FALSE;
    Serial.println("ALERT! EKG CRITICALLY OUT OF RANGE.");
  }

  // everything in range
  if (noWarnings) {
    Serial.println("There are no warnings to report.");
  }
}

//// Task functions ////

void commandTaskFunction(void* data) {
  CommandData* commandDataPtr = (CommandData*) data;
  char command = tolower(*commandDataPtr->remoteCommandPtr);
  DEBUG("Received command: ");
  DEBUGLN((char) command);

  if (command == 'i') {
    if (remoteInitialized) {
      Serial.println("E: remote connection already initialized.");
    } else {
      remoteInitialized = TRUE;
      Serial.println("Name of product: NFJ Doctor at Yo Fingertips");
      Serial.println("Patient: Poopy");
      Serial.println("Doctor: D. Scoop");
    }
  } else if (command == 's') { // START
    if (!remoteInitialized) {
      Serial.println("E: remote connection not initialized.");
    } else {
      Serial.println("Starting regular measurements");
      regularMeasurements = 1;
    }
  } else if (command == 'p') { // STOP
    if (!remoteInitialized) {
      Serial.println("E: remote connection not initialized.");
    } else {
      Serial.println("Stopping regular measurements");
      regularMeasurements = 0;
    }
  } else if (command == 'd') { // display
    // if currently @ display, remove
    // else add display task to scheduler
    if (!remoteInitialized) {
      Serial.println("E: remote connection not initialized.");
    } else {
      Serial.println("Toggling display");
      displayEnabled = !displayEnabled;
      addTask(displayTaskFunction, &displayData);
    }
  } else if (command == 'm') { // measurement
    if (!remoteInitialized) {
      Serial.println("E: remote connection not initialized.");
    } else {
      printMeasured(commandDataPtr);
    }
  } else if (command == 'w') { // warnings & alarms
    if (!remoteInitialized) {
      Serial.println("E: remote connection not initialized.");
    } else {
      printWarnings();
    }
  } else {
    Serial.print("E: unrecognized command.");
  }

  deleteCurrentTask = TRUE;
}

void remoteCommunicationsTaskFunction(void* data) {
  RemoteCommunicationsData* remoteDataPtr = (RemoteCommunicationsData*) data;

  // pg 26: TODO delete comment
  // initialize network interface
  // connect to / configure LAN network
  // handler to communicate w/ remote system
  // Format the data to be displayed and send the formatted data over the network for display on the remote terminal
  // continually update data @ 5 second rate

  if (Serial.available()) {
    *remoteDataPtr->remoteCommandPtr = Serial.read();

    addTask(commandTaskFunction, &commandData);
  }
}
