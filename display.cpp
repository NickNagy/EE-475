#include <Elegoo_GFX.h>    // Core graphics library
#include <Elegoo_TFTLCD.h> // Hardware-specific library
#include <TouchScreen.h>

#include <util.h>
#include <constants.h>

#include "globals.h"
#include "tasks.h"
#include "lcd.h"

// Private variables for display and keypad
Elegoo_GFX_Button buttons[8];
// constants for # of buttons per display mode
unsigned short numberOfButtons[] = {2, 6, 2, 6};
unsigned char batteryStr[6];

// Handler for a button press
void onButtonPressed(TFTKeyPadData* tftDataPtr, unsigned short b) {
  Bool addDisplay = TRUE;

  // Do the actual operation
  if (*tftDataPtr->displayModePtr == DISPLAY_MODE_SELECT) {
    if (b == 0) {
      *tftDataPtr->displayModePtr = DISPLAY_MENU;
      tft.fillScreen(BLACK);
    } else {
      *tftDataPtr->displayModePtr = DISPLAY_ANNUNCIATE;
      tft.fillScreen(BLACK);
    }
  } else if (*tftDataPtr->displayModePtr == DISPLAY_MENU) {
    if (b == numberOfButtons[DISPLAY_MENU] - 1) {
      // The last button goes back
      *tftDataPtr->displayModePtr = DISPLAY_MODE_SELECT;
      tft.fillScreen(BLACK);
    } else {
      // Otherwise queue the communications task
      addDisplay = FALSE;

      *tftDataPtr->displayModePtr = DISPLAY_ANNUNCIATE;
      tft.fillScreen(BLACK);

      // Add communications task
      tftDataPtr->measurementSelectionPtr[0] = b;
      *tftDataPtr->measurementLengthPtr      = 1;
      addTask(communicationsTaskFunction, &communicationsData);
    }
  } else if (*tftDataPtr->displayModePtr == DISPLAY_ANNUNCIATE) {
    // TODO fix
    if (b == 0) {
      *tftDataPtr->displayModePtr = DISPLAY_ACK_SELECT;
      tft.fillScreen(BLACK);
    }
    else if (b == 1) {
      *tftDataPtr->displayModePtr = DISPLAY_MODE_SELECT;
      tft.fillScreen(BLACK);
    }
  } else if (*tftDataPtr->displayModePtr == DISPLAY_ACK_SELECT) {
    switch (b) {
      case 0:
        tempAcknowledged = 1;
        break;
      case 1:
        bpAcknowledged = 1;
        break;
      case 2:
        pulseAcknowledged = 1;
        break;
      case 3:
        respirationAcknowledged = 1;
        break;
    }
    *tftDataPtr->displayModePtr = DISPLAY_ANNUNCIATE;
    tft.fillScreen(BLACK);
  } else {
    Serial.println("Invalid display mode");
  }

  if (addDisplay) addTask(displayTaskFunction, &displayData);
}

void drawButtons(unsigned short displayMode) {
  switch (displayMode) {
    case DISPLAY_MODE_SELECT:
      // tft, x, y, w, h, outline color, fill color, text color, text, text size
      // draw buttons for menu and annunciate
      buttons[0].initButton(&tft, tft.width()/2, 90, 150, 25, WHITE, BLACK, WHITE, "Menu", 2);
      buttons[1].initButton(&tft, tft.width()/2, 150, 150, 25, WHITE, BLACK, WHITE, "Display", 2);
      break;
    case DISPLAY_MENU:
    case DISPLAY_ACK_SELECT:
      // draw buttons for different measurements
      buttons[COMM_TEMPERATURE].initButton(&tft, tft.width()/2, 40, 150, 25, WHITE, BLACK, WHITE, "Temp", 2);
      buttons[COMM_PRESSURE].initButton(&tft, tft.width()/2, 80, 150, 25, WHITE, BLACK, WHITE, "BP", 2);
      buttons[COMM_PULSE].initButton(&tft, tft.width()/2, 120, 150, 25, WHITE, BLACK, WHITE, "Pulse", 2);
      buttons[COMM_RESP].initButton(&tft, tft.width()/2, 160, 150, 25, WHITE, BLACK, WHITE, "Resp", 2);
      buttons[COMM_EKG].initButton(&tft, tft.width()/2, 200, 150, 25, WHITE, BLACK, WHITE, "EKG", 2);
      buttons[5].initButton(&tft, tft.width()/2, 250, 150, 25, ORANGE, BLACK, ORANGE, "Back", 2);
      break;
    case DISPLAY_ANNUNCIATE:
      // Add buttons
      buttons[0].initButton(&tft, tft.width()/4, 260, tft.width()/2 - 20, 30, RED, BLACK, RED, "Ack", 2);
      buttons[1].initButton(&tft, tft.width()*3/4, 260, tft.width()/2 - 20, 30, ORANGE, BLACK, ORANGE, "Home", 2);
      break;
  }

  // Draw buttons
  for (uint8_t b = 0; b < numberOfButtons[displayMode]; b++) {
    buttons[b].drawButton();
  }
}

void drawAnnunciation(DisplayData* displayDataPtr) {
  // NOTE: old flashing logic
  // if (bpAlarmRange && !acknowledged) {
  //   tft.setTextColor(RED, BLACK);
  // } else if (bpOutOfRange || (bpAlarmRange && acknowledged)) {
  //   if (bpFlashWhite) {
  //     tft.setTextColor(WHITE, BLACK);
  //   } else {
  //     tft.setTextColor(ORANGE, BLACK);
  //   }
  // } else {
  //   tft.setTextColor(GREEN, BLACK);
  // }

  // TODO: create a WARNING button on the display page
  // TODO: fix locations of buttons, add RESPIRATION button
  // TODO just fix all of this lmao

  // First line: Temperature
  if (tempAlarmRange && !tempAcknowledged)           tft.setTextColor(RED, BLACK);
  else if (tempAlarmRange || tempWarningRange)    tft.setTextColor(ORANGE, BLACK);
  else                          tft.setTextColor(GREEN, BLACK);
  if (tempOn) {
    tft.setCursor(0,TEMP_DISP_Y);
    tft.print("Body Temperature: ");
    tft.setCursor(LEFT_JUSTIF, TEMP_DISP_Y+DATA_LINE_SKIP);
    tft.print((char*) displayDataPtr->tempCorrectedBufPtr[(tempBufferIndex-1)%BUF_LENGTH]);
    tft.print(" C");
  } else {
    tft.fillRect(0, TEMP_DISP_Y, tft.width(), DATA_LINE_SKIP*2, BLACK);
  }

  // Second Line: Systolic and Diastolic pressure
  if (bpAlarmRange && !bpAcknowledged)           tft.setTextColor(RED, BLACK);
  else if (bpAlarmRange || bpWarningRange)    tft.setTextColor(ORANGE, BLACK);
  else                          tft.setTextColor(GREEN, BLACK);
  if (bpOn) {
    tft.setCursor(0, SP_DISP_Y);
    tft.print("Systolic Pressure: ");
    tft.setCursor(LEFT_JUSTIF, SP_DISP_Y+DATA_LINE_SKIP);
    tft.print((char*) displayDataPtr->bloodPressCorrectedBufPtr[(pressureBufferIndex-1)%BUF_LENGTH]);
    tft.println(" mm Hg ");

    tft.setCursor(0, DP_DISP_Y);
    tft.print("Diastolic Pressure: ");
    tft.setCursor(LEFT_JUSTIF, DP_DISP_Y+DATA_LINE_SKIP);
    tft.print((char*) displayDataPtr->bloodPressCorrectedBufPtr[(pressureBufferIndex-1)%BUF_LENGTH+BUF_LENGTH]);
    tft.print(" mm Hg ");
  } else {
    tft.fillRect(0, SP_DISP_Y, tft.width(), DATA_LINE_SKIP*2, BLACK);
    tft.fillRect(0, DP_DISP_Y, tft.width(), DATA_LINE_SKIP*2, BLACK);
  }

  // Third Line: Pulse Rate
  if (pulseAlarmRange && !pulseAcknowledged)           tft.setTextColor(RED, BLACK);
  else if (pulseAlarmRange || pulseWarningRange)    tft.setTextColor(ORANGE, BLACK);
  else                          tft.setTextColor(GREEN, BLACK);
  if (pulseRateOn) {
    tft.setCursor(0, PULSE_DISP_Y);
    tft.print("Heart Rate: ");
    tft.print((char*) displayDataPtr->prCorrectedBufPtr[(pulseBufferIndex-1)%BUF_LENGTH]);
    tft.print(" BPM ");
  } else {
    tft.fillRect(0, PULSE_DISP_Y, tft.width(), DATA_LINE_SKIP*2, BLACK);
  }

  // Fourth Line: Respiration Rate
  if (respirationAlarmRange && !respirationAcknowledged)            tft.setTextColor(RED, BLACK);
  else if (respirationAlarmRange)   tft.setTextColor(ORANGE, BLACK);
  else                                  tft.setTextColor(GREEN, BLACK);
  tft.setCursor(0, RESP_DISP_Y);
  tft.print("Respiration Rate: ");
  tft.setCursor(LEFT_JUSTIF, RESP_DISP_Y+DATA_LINE_SKIP);
  tft.print((char*) displayDataPtr->respirationRateCorrectedBufPtr[(rrBufferIndex-1)%BUF_LENGTH]);
  tft.print(" Breaths Per Min ");

  // Fifth Line: EKG
  tft.setTextColor(GREEN, BLACK);
  tft.setCursor(0, EKG_DISP_Y);
  tft.print("EKG Rate: ");
  tft.setCursor(LEFT_JUSTIF, EKG_DISP_Y+DATA_LINE_SKIP);
  tft.print((char*) displayDataPtr->EKGFreqBufPtr[(EKGFreqBufferIndex-1)%(BUF_LENGTH*2)]);
  tft.print(" Hz");

  // Sixth Line: Battery Status
  if (battLow)  tft.setTextColor(RED, BLACK);
  else          tft.setTextColor(GREEN, BLACK);
  tft.setCursor(0, BATT_DISP_Y);
  // tft.fillRect(0, BATT_DISP_Y, tft.width(), DATA_LINE_SKIP, BLACK);
  tft.print("Battery: ");
  sprintf(batteryStr, "%03d%%", *displayDataPtr->batteryStatePtr);
  tft.print((char*) batteryStr);
}

// NOTE: CITATION
// The code for the keypad and display for utilizing buttons and detecting
// button presses was largely structured based on the Phone Call example as
// provided by the TouchScreen library.
//
// Source code referenced:
// https://class.ee.washington.edu/474/peckol/doc/TFT-Display/Example06-Phonecal/phonecal-1/phonecal-1.ino

void displayTaskFunction(void* data) {
  if (displayEnabled) {
    DisplayData* displayDataPtr = (DisplayData*) data;

    if (*displayDataPtr->displayModePtr == DISPLAY_ANNUNCIATE) {
      drawAnnunciation(displayDataPtr);
    }
    drawButtons(*displayDataPtr->displayModePtr);
  } else {
    tft.fillScreen(BLACK);
  }

  deleteCurrentTask = TRUE;
}

void tftKeyPadTaskFunction(void* data) {
  if (displayEnabled) {
    TFTKeyPadData* tftDataPtr = (TFTKeyPadData*) data;

    // Set pin 13 to HIGH/LOW to read the pressure point
    digitalWrite(13, HIGH);
    TSPoint p = ts.getPoint();
    digitalWrite(13, LOW);

    pinMode(XM, OUTPUT);
    pinMode(YP, OUTPUT);

    if (p.z > MINPRESSURE && p.z < MAXPRESSURE) {
      // scale from 0->1023 to tft.width
      int tx = p.x;
      int ty = p.y;

      p.x = tft.width() - map(ty, TS_MINY, TS_MAXY, 0, tft.width());
      p.y = map(tx, TS_MINX, TS_MAXX, 0, tft.height());
    }

    // go thru all the buttons, checking if they were pressed
    for (uint8_t b=0; b<numberOfButtons[*tftDataPtr->displayModePtr]; b++) {
      buttons[b].press(buttons[b].contains(p.x, p.y));
    }

    // now we can ask the buttons if their state has changed
    for (uint8_t b=0; b<numberOfButtons[*tftDataPtr->displayModePtr]; b++) {
      if (buttons[b].justReleased()) {
        buttons[b].drawButton();  // draw normal
      }

      if (buttons[b].justPressed()) {
        buttons[b].drawButton(true);  // draw invert!
        onButtonPressed(tftDataPtr, b);
        // TODO potensh move this elsewhere
        delay(100);

        // cannot be pressing more than one button at a time
        break;
      }
    }
  }
}
