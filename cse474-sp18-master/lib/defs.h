#ifndef _DEFS_H
#define _DEFS_H

#include <constants.h>

// Boolean
typedef enum _myBool { FALSE = 0, TRUE = 1 } Bool;

// Task struct
typedef struct _tcb_struct {
  void (*taskFn)(void*);
  void* taskDataPtr;
  char* taskName;
  // for linked-list... TCB nodes have an associated prev and next node
  struct _tcb_struct* next;
  struct _tcb_struct* prev;
} TCB;

// Complex number
typedef struct _ComplexData {
  int real;
  int imag;
} Complex;

// Intrasystem communications
typedef struct _Request {
  unsigned int startOfMessage;
  unsigned int endOfMessage;
  unsigned long taskIdentifier;
  unsigned short function;
  unsigned long functionData;
} Request;

typedef struct _Response {
  unsigned int startOfMessage;
  unsigned int endOfMessage;
  unsigned long taskIdentifier;
  unsigned short function;
  unsigned int resultData;
} Response;

typedef struct _EKGResponse {
  unsigned int startOfMessage;
  unsigned int endOfMessage;
  unsigned long taskIdentifier;
  unsigned short function;
  unsigned int EKGRawData[EKG_N];
} EKGResponse;

#endif /* end of include guard: _DEFS_H */
