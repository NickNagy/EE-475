#ifndef _SCHEDULE_H
#define _SCHEDULE_H

#include <defs.h>

typedef struct _ScheduleList {
	TCB* head;
	TCB* tail;
  void insertTask(TCB* node);
  void deleteTask(TCB* node);
} ScheduleList;

#endif
