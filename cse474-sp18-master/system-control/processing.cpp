#include <math.h>

#include <defs.h>
#include <constants.h>
#include <util.h>

#include "tasks.h"
#include "globals.h"

// for FFT, this is the array of frequencies
Complex output[EKG_N];

void FFT(EKGProcessingData* ekgProcessingDataPtr) {
  // DFT formula:
  //      x_n = EKGRawBufPtr[n] + 0i
  //      output_k = sum_{n = 0}^{N-1} (x_n * (cos (...) - i sin(...)))

  DEBUGLN("Computing Discrete Fourier Transform...");

  for (int k = 0; k < EKG_N; k++) {
    for (int n = 0; n < EKG_N; n++) {
      float theta = ((n*k*2.0)*M_PI)/(float)(EKG_N);
      int r = ekgProcessingDataPtr->EKGRawBufPtr[n];
      output[k].real += r*cos(theta);
      output[k].imag -= r*sin(theta);
    }
    if (!(k % (EKG_N/8))) {
      DEBUG(".");
    }
  }
  DEBUGLN("");
}

// Find the max frequency
void getFrequency(EKGProcessingData* ekgProcessingDataPtr) {
  unsigned long sampleFreq = *ekgProcessingDataPtr->EKGSampleFreqPtr;
  unsigned long signalFreq;
  int maxVal = 0;
  int maxIndex = 0;

  // find index of max magnitude in x
  for (int i = 0; i < EKG_N/2; i++) { // half-range
    int magnitude = sqrt(pow(output[i].real,2) + pow(output[i].imag,2));
    if (magnitude > maxVal) {
      maxIndex = i;
      maxVal = magnitude;
    }
  }
  signalFreq = (sampleFreq * maxIndex) / EKG_N;

  DEBUG("sampleFreq: ");
  DEBUG(sampleFreq);
  DEBUG(" signalFreq: ");
  DEBUG(signalFreq);
  DEBUG(" max index: ");
  DEBUGLN(maxIndex);

  // Convert to string and store
  if (nullptr == ekgProcessingDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex]) {
    ekgProcessingDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex] = (unsigned char*) malloc(20);
  }
  sprintf(ekgProcessingDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex], "%d", signalFreq);

  EKGFreqBufferIndex = (EKGFreqBufferIndex + 1) % (BUF_LENGTH*2);
}

////// Task functions //////

void computeTaskFunction(void* data) {
  ComputeData* computeDataPtr = (ComputeData*) data;

  int i;
  for (i = 0; i < *computeDataPtr->measurementLengthPtr; i++) {
    switch (computeDataPtr->measurementSelectionPtr[i]) {
      case COMM_TEMPERATURE:
        if (nullptr == computeDataPtr->tempCorrectedBufPtr[tempBufferIndex]) {
          computeDataPtr->tempCorrectedBufPtr[tempBufferIndex] = (unsigned char*) malloc(20);
        }
        sprintf(computeDataPtr->tempCorrectedBufPtr[tempBufferIndex], "%d",
          (unsigned int)(computeDataPtr->temperatureRawBufPtr[tempBufferIndex]*0.75 + 5));

        tempBufferIndex = (tempBufferIndex + 1) % BUF_LENGTH;
        break;
      case COMM_PRESSURE:
        if (nullptr == computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex]) {
          computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex] = (unsigned char*) malloc(20);
        }
        if (nullptr == computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex+BUF_LENGTH]) {
          computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex+BUF_LENGTH] = (unsigned char*) malloc(20);
        }
        sprintf(computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex], "%d",
          (unsigned int)(computeDataPtr->bloodPressRawBufPtr[pressureBufferIndex]*2 + 9));
        sprintf(computeDataPtr->bloodPressCorrectedBufPtr[pressureBufferIndex+BUF_LENGTH], "%d",
          (unsigned int)(computeDataPtr->bloodPressRawBufPtr[pressureBufferIndex+BUF_LENGTH]*1.5 + 6));

        pressureBufferIndex = (pressureBufferIndex + 1) % BUF_LENGTH;
        break;
      case COMM_PULSE:
        if (nullptr == computeDataPtr->prCorrectedBufPtr[pulseBufferIndex]) {
          computeDataPtr->prCorrectedBufPtr[pulseBufferIndex] = (unsigned char*) malloc(20);
        }
        sprintf(computeDataPtr->prCorrectedBufPtr[pulseBufferIndex], "%d",
          (unsigned int)(computeDataPtr->pulseRateRawBufPtr[pulseBufferIndex]*3 + 8));

        pulseBufferIndex = (pulseBufferIndex + 1) % BUF_LENGTH;
        break;
      case COMM_RESP:
        if (nullptr == computeDataPtr->respirationRateCorrectedBufPtr[rrBufferIndex]) {
          computeDataPtr->respirationRateCorrectedBufPtr[rrBufferIndex] = (unsigned char*) malloc(20);
        }
        sprintf(computeDataPtr->respirationRateCorrectedBufPtr[rrBufferIndex], "%d",
          (unsigned int)(computeDataPtr->respirationRateRawBufPtr[rrBufferIndex]*3 + 7));

        rrBufferIndex = (rrBufferIndex + 1) % BUF_LENGTH;
        break;
      case COMM_EKG:
        if (nullptr == computeDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex]) {
          computeDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex] = (unsigned char*) malloc(20);
        }
        sprintf(computeDataPtr->EKGFreqBufPtr[EKGFreqBufferIndex], "...");
        break;
      default:
        Serial.println("Invalid measurement selector");
        break;
    }
  }

  *computeDataPtr->measurementLengthPtr = 0;
  deleteCurrentTask = TRUE;
}

void EKGProcessTaskFunction(void* data) {
  EKGProcessingData* ekgProcessingDataPtr = (EKGProcessingData*) data;

  FFT(ekgProcessingDataPtr);
  getFrequency(ekgProcessingDataPtr);

  addTask(displayTaskFunction, &displayData);

  deleteCurrentTask = TRUE;
}
