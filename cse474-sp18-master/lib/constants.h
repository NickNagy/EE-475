#ifndef _CONSTANTS_H
#define _CONSTANTS_H

// For the Arduino pins
#if defined(ARDUINO) && (ARDUINO >= 100)
#include "Arduino.h"
#else
#include "WProgram.h"
#endif

#define BUF_LENGTH 8
#define EKG_N     256

// constants
#define TEMP_UPPER_LIM 50
#define TEMP_LOWER_LIM 25
#define SP_UPPER_LIM 150
#define SP_LOWER_LIM 110
#define DP_UPPER_LIM 80
#define DP_LOWER_LIM 50
#define PR_UPPER_LIM 40
#define PR_LOWER_LIM 15

// constants for transducer
#define TRANS_UPPER_LIM 200
#define TRANS_LOWER_LIM 10

// Constants for the warning/alarm system
#define TEMP_SAFE_HIGH 40 // 37.8
#define TEMP_SAFE_LOW 34 // 36.1
#define SP_SAFE_LOW 120
#define SP_SAFE_HIGH 130
#define DP_SAFE_LOW 70
#define DP_SAFE_HIGH 80
#define PR_SAFE_HIGH 100
#define PR_SAFE_LOW 60
#define RR_SAFE_HIGH 25
#define RR_SAFE_LOW 12
#define EKG_SAFE_HIGH 3500
#define EKG_SAFE_LOW 35
#define BATT_SAFE 20

// Constants for display
#define DISPLAY_MODE_SELECT 0
#define DISPLAY_MENU        1
#define DISPLAY_ANNUNCIATE  2
#define DISPLAY_ACK_SELECT  3

// constants for button locations
#define TEMP_DISP_Y 0
#define SP_DISP_Y 40
#define DP_DISP_Y 80
#define PULSE_DISP_Y 120
#define RESP_DISP_Y 140
#define EKG_DISP_Y  180
#define BATT_DISP_Y 220
#define DATA_LINE_SKIP 20

// Interval for scheduler
#define SCHED_INTERVAL 500

// EKG constant
#define EKG_INTERVAL      120 // in millis: 140 is upper limit to measure 3.5kHz
#define EKG_SAMPLE_FREQ   1000000 / EKG_INTERVAL

// Constants for communications
#define COMM_TEMPERATURE  0
#define COMM_PRESSURE     1
#define COMM_PULSE        2
#define COMM_RESP         3
#define COMM_EKG          4
#define PERIPHERAL_RX     11
#define PERIPHERAL_TX     12
#define SYSCONTROL_RX     A12
#define SYSCONTROL_TX     A11

#endif /* end of include guard: _CONSTANTS_H */
