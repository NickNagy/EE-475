#ifdef _CONSTANTS_H
#define _CONSTANTS_H


#define BUF_LENGTH 16
typedef enum _myBool { FALSE = 0, TRUE = 1 } Bool;
//measurement max and min values

//spectrum and event
#define SPEC_LOW 500
#define SPEC_HIGH 1000
#define EVNT_LOW 0
#define EVNT_HIGH 9999

//frequency
#define FREQ_H_MAX 1000000
#define FREQ_H_LOW 0
#define FREQ_L_MAX 100
#define FREQ_L_LOW 0
#define FREQ_H_RANGE 1000
#define FREQ_L_RANGE 0.1

//period
#define PER_H_MAX 0.01
#define PER_H_LOW 0
#define PER_L_MAX 1
#define PER_L_LOW 0
#define PER_H_RANGE 0.00001
#define PER_L_RANGE 0.01

//time-interval
#define TIME_H_MAX 0.01
#define TIME_H_LOW 0
#define TIME_L_MAX 1
#define TIME_L_LOW 0
#define TIME_H_RANGE 0.00001
#define TIME_L_RANGE 0.01



//constants for display
#define DISPLAY_MAIN 0
#define DISPLAY_MENU 1
#define DISPLAY_MEASUREMENTS 2
//constants for communications

#define COMM_NO 0
#define COMM_FREQ 1
#define COMM_PRD 2
#define COMM_TIME 3
#define COMM_SPEC 4
#define COMM_EVNT 5

#endif
