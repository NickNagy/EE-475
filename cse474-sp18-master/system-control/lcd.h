#ifndef _LCD_H
#define _LCD_H

#include <Elegoo_GFX.h>
#include <Elegoo_TFTLCD.h>
#include <TouchScreen.h>

// The control pins for the LCD can be assigned to any digital or
// analog pins...but we'll use the analog pins as this allows us to
// double up the pins with the touch screen (see the TFT paint example).
#define LCD_CS A3 // Chip Select goes to Analog 3
#define LCD_CD A2 // Command/Data goes to Analog 2
#define LCD_WR A1 // LCD Write goes to Analog 1
#define LCD_RD A0 // LCD Read goes to Analog 0

#define LCD_RESET A4 // Can alternately just connect to Arduino's reset pin

// Assign human-readable names to some common 16-bit color values:
#define BLACK   0x0000
#define BLUE    0x001F
#define RED     0xF800
#define ORANGE  0xFFA5 // TODO: check if right shade
#define GREEN   0x07E0
#define CYAN    0x07FF
#define MAGENTA 0xF81F
#define YELLOW  0xFFE0
#define WHITE   0xFFFF

// TouchScreen constants
#define YP A2  // must be an analog pin, use "An" notation!
#define XM A3  // must be an analog pin, use "An" notation!
#define YM 8   // can be a digital pin
#define XP 9   // can be a digital pin
#define TS_MINX 70
#define TS_MAXX 920
#define TS_MINY 120
#define TS_MAXY 900
#define STATUS_X 65
#define STATUS_Y 10
#define MINPRESSURE 10
#define MAXPRESSURE 1000

// Constants for TFT cursor
#define LEFT_JUSTIF 20

// LCD setup
void setupLcd();

// Advertizing data in tasks.c
extern Elegoo_TFTLCD tft;
extern TouchScreen ts;

#endif
