#include <TimerOne.h>

#include <constants.h>
#include <util.h>

#include "globals.h"
#include "lcd.h"
#include "tasks.h"

// GLOBAL VARIABLES FOR THE SYSTEM CONTROL SUBSYSTEM

// raw data
unsigned int temperatureRawBuf[BUF_LENGTH];
unsigned int bloodPressRawBuf[BUF_LENGTH*2];
unsigned int pulseRateRawBuf[BUF_LENGTH];
unsigned int respirationRateRawBuf[BUF_LENGTH];
unsigned int EKGRawBuf[256];
unsigned int EKGSampleFreq;

// corrected data
unsigned char* tempCorrectedBuf[BUF_LENGTH];
unsigned char* bloodPressCorrectedBuf[BUF_LENGTH*2];
unsigned char* pulseRateCorrectedBuf[BUF_LENGTH];
unsigned char* respirationRateCorrectedBuf[BUF_LENGTH];
unsigned char* EKGFreqBuf[BUF_LENGTH*2];

// tft keypad
unsigned short functionSelect;
// unsigned short measurementSelection;
unsigned short measurementSelection[8];
unsigned short measurementLength;

// status
unsigned short batteryState;

// display
unsigned short displayMode;

// communications
SoftwareSerial peripheralSerial(SYSCONTROL_RX, SYSCONTROL_TX);

// Remote comms
char remoteCommand;

//////// Private variables ////////

// For scheduling: should fire every 0.5 sec
unsigned long timeBase;
unsigned long lastTick;
unsigned long tickCount;

void tick() {
  tickCount = (tickCount + 1) % 10; // this is 5000 (max interval needed) / 500 (interval of tick)

  Bool refresh = FALSE;

  if (!tickCount) {
    // add tasks
    addTask(statusTaskFunction, &statusData);
    addTask(warningAlarmTaskFunction, &warningAlarmData);

    // Regular measurements for remote display
    if (regularMeasurements) {
      int i;
      for (i = 0; i < 5; i++) { // TODO constant for # of measurements? lol
        measurementSelection[i] = i;
      }
      measurementLength = 5;

      addTask(communicationsTaskFunction, &communicationsData);
    }
  }

  if (displayMode == DISPLAY_ANNUNCIATE) {
    // Scheduler logic
    if (!tickCount) {
      refresh = TRUE;
    }

    // Warning logic
    if (pulseWarningRange && !pulseAlarmRange && !(tickCount % 4)) {
      // flash pulse rate
      pulseRateOn = !pulseRateOn;
      refresh = TRUE;
    }
    if (tempWarningRange && !tempAlarmRange && !(tickCount % 2)) {
      // flash temperature
      tempOn = !tempOn;
      refresh = TRUE;
    }
    // NOTE bumped time because otherwise display takes too long!
    if (bpWarningRange && !bpAlarmRange && !(tickCount % 2)) {
      // flash blood pressure
      bpOn = !bpOn;
      refresh = TRUE;
    }
  }

  // After the logic of refreshing is evaluated, queue up the display task
  if (refresh) {
    addTask(displayTaskFunction, &displayData);
  }
}

//////// Public helper functions ////////

// Add a new task to the scheduler
void addTask(void (*taskFn)(void*), void* taskDataPtr) {
  TCB* task = (TCB*) malloc(sizeof(TCB));
  task->taskFn      = taskFn;
  task->taskDataPtr = taskDataPtr;
  task->taskName    = (char*) malloc(20);
  if (taskDataPtr == &computeData) {
    sprintf(task->taskName, "Compute");
  } else if (taskDataPtr == &displayData) {
    sprintf(task->taskName, "Display");
  } else if (taskDataPtr == &warningAlarmData) {
    sprintf(task->taskName, "Warning");
  } else if (taskDataPtr == &statusData) {
    sprintf(task->taskName, "Status");
  } else if (taskDataPtr == &tftKeyPadData) {
    sprintf(task->taskName, "Tft");
  } else if (taskDataPtr == &communicationsData) {
    sprintf(task->taskName, "Comms");
  } else if (taskDataPtr == &ekgProcessingData) {
    sprintf(task->taskName, "EKG");
  } else if (taskDataPtr == &remoteCommsData) {
    sprintf(task->taskName, "Remote");
  } else if (taskDataPtr == &commandData) {
    sprintf(task->taskName, "Command");
  }
  task->next        = nullptr;
  task->prev        = nullptr;
  scheduleList.insertTask(task);
}

//////// Helper functions ////////

// Initial values for global variables
void initializeValues() {
  // raw buffers
  // TODO changing init values to be safe
  temperatureRawBuf[BUF_LENGTH-1] = 37;
  bloodPressRawBuf[BUF_LENGTH-1] = 125;
  bloodPressRawBuf[2*BUF_LENGTH-1] = 75;
  pulseRateRawBuf[BUF_LENGTH-1] = 80;
  respirationRateRawBuf[BUF_LENGTH-1] = 17;
  int i;
  for (i = 0; i < EKG_N; i++) {
    EKGRawBuf[i] = 0;
  }
  EKGSampleFreq = EKG_SAMPLE_FREQ;

  // compute
  for (i = 0; i < BUF_LENGTH; i++) {
    tempCorrectedBuf[i] = nullptr;
    bloodPressCorrectedBuf[i] = nullptr;
    bloodPressCorrectedBuf[i+BUF_LENGTH] = nullptr;
    pulseRateCorrectedBuf[i] = nullptr;
    respirationRateCorrectedBuf[i] = nullptr;
  }

  // tft keypad
  functionSelect = 0;
  measurementLength = 0;

  // status
  batteryState = 200;

  // warning count
  warningCount = 0;

  // display
  displayMode = DISPLAY_MODE_SELECT;

  remoteCommand = 0;
  displayEnabled = 1;

  // warning and alarms
  pulseWarningRange = 0;
  tempWarningRange = 0;
  bpWarningRange = 0;
  bpAlarmRange = 0;
  tempAlarmRange = 0;
  pulseAlarmRange = 0;
  respirationAlarmRange = 0;
  EKGAlarmRange = 0;
  battLow = 0;

  tempAcknowledged = 0;
  bpAcknowledged = 0;
  pulseAcknowledged = 0;
  respirationAcknowledged = 0;

  pulseRateOn = 1;
  tempOn = 1;
  bpOn = 1;

  tempNewMeasurement = 1;
  bpNewMeasurement = 1;
  pulseNewMeasurement = 1;
  respirationNewMeasurement = 1;

  tempAlarmCount = 0;
  bpAlarmCount = 0;
  pulseAlarmCount = 0;
  respirationAlarmCount = 0;

  // schedule list
  deleteCurrentTask = FALSE;

  // index
  tempBufferIndex = 0;
  pressureBufferIndex = 0;
  pulseBufferIndex = 0;
  rrBufferIndex = 0;
  EKGFreqBufferIndex = 0;
}

// Initialize data structs' pointers to global variables
void initializeDataStructs() {
  computeData.temperatureRawBufPtr            = temperatureRawBuf;
  computeData.bloodPressRawBufPtr             = bloodPressRawBuf;
  computeData.pulseRateRawBufPtr              = pulseRateRawBuf;
  computeData.respirationRateRawBufPtr        = respirationRateRawBuf;
  computeData.EKGRawBufPtr                    = EKGRawBuf;
  computeData.EKGSampleFreqPtr                = &EKGSampleFreq;
  computeData.tempCorrectedBufPtr             = tempCorrectedBuf;
  computeData.bloodPressCorrectedBufPtr       = bloodPressCorrectedBuf;
  computeData.prCorrectedBufPtr               = pulseRateCorrectedBuf;
  computeData.respirationRateCorrectedBufPtr  = respirationRateCorrectedBuf;
  computeData.EKGFreqBufPtr                   = EKGFreqBuf;
  computeData.measurementSelectionPtr         = measurementSelection;
  computeData.measurementLengthPtr            = &measurementLength;

  displayData.tempCorrectedBufPtr             = tempCorrectedBuf;
  displayData.bloodPressCorrectedBufPtr       = bloodPressCorrectedBuf;
  displayData.prCorrectedBufPtr               = pulseRateCorrectedBuf;
  displayData.respirationRateCorrectedBufPtr  = respirationRateCorrectedBuf;
  displayData.EKGFreqBufPtr                   = EKGFreqBuf;
  displayData.batteryStatePtr                 = &batteryState;
  displayData.displayModePtr                  = &displayMode;

  warningAlarmData.temperatureRawBufPtr     = temperatureRawBuf;
  warningAlarmData.bloodPressRawBufPtr      = bloodPressRawBuf;
  warningAlarmData.pulseRateRawBufPtr       = pulseRateRawBuf;
  warningAlarmData.respirationRateRawBufPtr = respirationRateRawBuf;
  warningAlarmData.batteryStatePtr          = &batteryState;

  tftKeyPadData.measurementSelectionPtr = measurementSelection;
  tftKeyPadData.measurementLengthPtr    = &measurementLength;
  tftKeyPadData.displayModePtr          = &displayMode;

  communicationsData.measurementSelectionPtr      = measurementSelection;
  communicationsData.measurementLengthPtr         = &measurementLength;
  communicationsData.peripheralSerialPtr          = &peripheralSerial;
  communicationsData.temperatureRawBufPtr         = temperatureRawBuf;
  communicationsData.bloodPressRawBufPtr          = bloodPressRawBuf;
  communicationsData.pulseRateRawBufPtr           = pulseRateRawBuf;
  communicationsData.respirationRateRawBufPtr     = respirationRateRawBuf;
  communicationsData.EKGRawBufPtr                 = EKGRawBuf;
  communicationsData.EKGSampleFreqPtr             = &EKGSampleFreq;

  statusData.batteryStatePtr  = &batteryState;

  ekgProcessingData.EKGRawBufPtr      = EKGRawBuf;
  ekgProcessingData.EKGSampleFreqPtr  = &EKGSampleFreq;
  ekgProcessingData.EKGFreqBufPtr     = EKGFreqBuf;

  remoteCommsData.remoteCommandPtr = &remoteCommand;

  commandData.remoteCommandPtr                = &remoteCommand;
  commandData.tempCorrectedBufPtr             = tempCorrectedBuf;
  commandData.bloodPressCorrectedBufPtr       = bloodPressCorrectedBuf;
  commandData.prCorrectedBufPtr               = pulseRateCorrectedBuf;
  commandData.respirationRateCorrectedBufPtr  = respirationRateCorrectedBuf;
  commandData.EKGFreqBufPtr                   = EKGFreqBuf;
  commandData.batteryStatePtr                 = &batteryState;
  commandData.measurementSelectionPtr         = measurementSelection;
  commandData.measurementLengthPtr            = &measurementLength;
}

//////// Kernel task functions ////////

void statusTaskFunction(void* data) {
  StatusData* statusDataPtr = (StatusData*) data;

  if (*statusDataPtr->batteryStatePtr > 0) {
    (*statusDataPtr->batteryStatePtr) --;
  }

  deleteCurrentTask = TRUE;
}

void printTaskQueue() {
  TCB* curr = scheduleList.head;
  while (nullptr != curr) {
    if (currentTask == curr) {
      Serial.print("*");
    }
    Serial.print(curr->taskName);
    Serial.print("->");

    curr = curr->next;
  }
  Serial.println();
}

void schedulerTaskFunction(void) {
  while (1) {
    // printTaskQueue();

    // TODO: this needs to be timed
    currentTask->taskFn(currentTask->taskDataPtr);

    TCB* completedTask = currentTask;

    // Reset to the head if we're at the end of the list
    if (nullptr != currentTask->next) {
      currentTask = currentTask->next;
    } else {
      currentTask = scheduleList.head;
    }

    // After moving on to the next task, we delete and clean up the task.
    if (deleteCurrentTask) {
      scheduleList.deleteTask(completedTask);
      free(completedTask->taskName);
      free(completedTask);
      deleteCurrentTask = FALSE;
    }

    // Every so often we want to run our periodic tasks:
    // Status, Display, Warning/Alarm
    unsigned long currTime = millis();
    if (currTime - lastTick > SCHED_INTERVAL) {
      tick();
      lastTick = currTime;
    }

    // if 8 hrs since start up, reset warning counter
    if (millis() - timeBase > 28800000) {
      warningCount = 0;
    }

    // TODO make sure this is fixed
    //delay_ms(300); // page 15 of spec, need to determine empirically
  }
}

void startupTaskFunction(void) {
  Serial.begin(9600);
  peripheralSerial.begin(9600);

  Serial.println("Hello world from System Control");

  initializeValues();
  initializeDataStructs();

  // Build Task Queue
  addTask(displayTaskFunction, &displayData);
  addTask(statusTaskFunction, &statusData);

  // Infinitely running tasks
  addTask(tftKeyPadTaskFunction, &tftKeyPadData);
  addTask(remoteCommunicationsTaskFunction, &remoteCommsData);

  // Time base management
  timeBase = millis();
  lastTick = timeBase;
  tickCount = 0;
  // Timer1.initialize(500 * 1000);

  // Set the current task in the schedule list
  currentTask = scheduleList.head;

  setupLcd();
}
