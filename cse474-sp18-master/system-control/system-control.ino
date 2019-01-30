#include <stdlib.h>

#include <defs.h>

#include "tasks.h"

void setup() {
  // Start with the Startup Task, which has a function but no data
  TCB* startupTask = (TCB*) malloc(sizeof(TCB));
  startupTask->taskFn = &startupTaskFunction;
  // Run the startup task
  startupTask->taskFn(startupTask->taskDataPtr);
  free(startupTask);

  // Run the schedule task
  TCB* scheduleTask = (TCB*) malloc(sizeof(TCB));
  scheduleTask->taskFn = &schedulerTaskFunction;
  scheduleTask->taskFn(scheduleTask->taskDataPtr);

  // this point should only be reached if the schedule task completes, which
  // should be never.
  Serial.println("Scheduler finished");
  free(scheduleTask);
}

void loop() {
}
