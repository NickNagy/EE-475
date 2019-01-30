#include <TimerOne.h>

#include <util.h>

#include "globals.h"
#include "tasks.h"

////// Task functions //////

// NOTE this is a periodic task that runs every so often
void warningAlarmTaskFunction(void* data) {
  WarningAlarmData* warningAlarmDataPtr = (WarningAlarmData*) data;

  // The latest correct value is the one that's one less than the current buffer index
  unsigned int tempRaw = warningAlarmDataPtr->temperatureRawBufPtr[(tempBufferIndex-1)%BUF_LENGTH];
  unsigned int spRaw = warningAlarmDataPtr->bloodPressRawBufPtr[(pressureBufferIndex-1)%BUF_LENGTH];
  unsigned int dpRaw = warningAlarmDataPtr->bloodPressRawBufPtr[(pressureBufferIndex-1)%BUF_LENGTH + BUF_LENGTH];
  unsigned int prRaw = warningAlarmDataPtr->pulseRateRawBufPtr[(pulseBufferIndex-1)%BUF_LENGTH];
  unsigned int rrRaw = warningAlarmDataPtr->respirationRateRawBufPtr[(rrBufferIndex-1)%BUF_LENGTH];

  //// First warnings
  pulseWarningRange = (prRaw < 0.95*PR_SAFE_LOW || prRaw > 1.05*PR_SAFE_HIGH);
  tempWarningRange = (tempRaw < 0.95*TEMP_SAFE_LOW || tempRaw > 1.05*TEMP_SAFE_HIGH);
  bpWarningRange = ((spRaw < 0.95*SP_SAFE_LOW || spRaw > 1.05*SP_SAFE_HIGH) || (dpRaw < 0.95*DP_SAFE_LOW || dpRaw > 1.05*DP_SAFE_HIGH));

  //// Next, alarms. This overrides warning
  // 1. Systolic blood pressure
  bpAlarmRange = (spRaw > 1.2*SP_SAFE_HIGH);
  // 2. Temp, pulse rate, respiration
  tempAlarmRange = (tempRaw > 1.15*TEMP_SAFE_HIGH || tempRaw < 0.85*TEMP_SAFE_LOW);
  pulseAlarmRange = (prRaw > 1.15*PR_SAFE_HIGH || prRaw < 0.85*PR_SAFE_LOW);
  respirationAlarmRange = (rrRaw > 1.15*RR_SAFE_HIGH || rrRaw < 0.85*RR_SAFE_LOW);

  if (tempAcknowledged) {
    // acknowledged has been pressed, but we need to count any abhorrent values still in the alarm range
    if (tempAlarmRange && tempNewMeasurement) {
      tempAlarmCount++;
    }
  }
  if (bpAcknowledged) {
    if (bpAlarmRange && bpNewMeasurement) {
      bpAlarmCount++;
    }
  }
  if (pulseAcknowledged) {
    if (pulseAlarmRange && pulseNewMeasurement) {
      pulseAlarmCount++;
    }
  }
  if (respirationAcknowledged) {
    if (respirationAlarmRange && respirationNewMeasurement) {
      respirationAlarmCount++;
    }
  }

  // Now evaluate if we've crossed the limit
  if (tempAlarmCount > 5) {
    tempAcknowledged = 0;
  }
  if (bpAlarmCount > 5) {
    bpAcknowledged = 0;
  }
  if (pulseAlarmCount > 5) {
    pulseAcknowledged = 0;
  }
  if (respirationAlarmCount > 5) {
    respirationAcknowledged = 0;
  }

  // Note that the new measurement has been handled
  tempNewMeasurement = bpNewMeasurement = pulseNewMeasurement = respirationNewMeasurement = 0;

  //// Finally, battery
  // TODO should this be in Warning-Alarm task?
  battLow = (*warningAlarmDataPtr->batteryStatePtr < BATT_SAFE);

  // if (pulseWarningRange || tempWarningRange || bpWarningRange) {
  //   // If we have any warnings at all, we have to initialize the timer interrupts
  //   // 500,000 microseconds = 0.5 sec
  //   Timer1.attachInterrupt(warningIsr);
  // } else {
  //   Timer1.detachInterrupt();
  // }

  // // initialize all color fields to GREEN, conditions below determine if change to RED
  //   tempOutOfRange = TRUE;
  //   warningCount++;
  //     if(acknowledged) {
  //       // if(highCount >= 5) {
  //       //   tempAlarmRange = TRUE;
  //       // } else {
  //       //   highCount++;
  //       // }
  //     } else {
  //       tempAlarmRange = TRUE;
  //     }
  //   }
  // } else {
  //   tempOutOfRange = FALSE;
  //   tempAlarmRange = FALSE;
  // }

  deleteCurrentTask = TRUE;
}
