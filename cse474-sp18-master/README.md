# cse474-sp18
Source code for UW CSE/EE 474 for Spring 2018. Nick Nagy, Hannah Fisher, Sarang Joshi.

## Source Code organization
```
.
├── lib
│   ├── constants.h             All predefined constants
│   ├── defs.h                  Struct definitions: tcb, complex numbers, request/response, etc.
│   └── util.cpp/.h             Utility functions: debugging, millisecond delay
├── peripheral
│   ├── measure.cpp/.h          Measuring peripheral data
│   └── peripheral.ino          PERIPHERAL ARDUINO FILE
├── README.md
└── system-control
    ├── comms.cpp               Intrasystem communications task
    ├── display.cpp             Tasks relating to on-system TFT keypad + display
    ├── globals.cpp/.h          Shared global variables
    ├── kernel.cpp              Main kernel tasks: schedule, startup, status; shared data variables
    ├── lcd.cpp/.h              LCD helper functions
    ├── processing.cpp          Compute/processing tasks for measured data
    ├── remote.cpp              Remote communications tasks
    ├── scheduleList.cpp/.h     Scheduler's list structure
    ├── system-control.ino      SYSTEM CONTROL ARDUINO FILE
    ├── tasks.h                 Miscellaneous task-related functions, data definitions, task function definitions
    └── warningAlarm.cpp        Warning/alarm reporting management tasks
```
