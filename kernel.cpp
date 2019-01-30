#include <constants.h>
#include <globals.h>



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
