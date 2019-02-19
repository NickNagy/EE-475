/*
 * File:   slave_main.c
 * Author: Nick Nagy, Nick Orlov
 *
 * Created on February 4, 2019, 3:23 PM
 */


#include <xc.h>
#include "spi.h"
#include "configvsmall.h"
#include "pic18f25k22.h"

//    first config attempt
//    // Configuring SSPCON register
//    SSPCON1bits.SSPM = 0b0100; //0100 = SPI Slave mode, clock = SCK pin, SS pin control enabled
//    SSPCON1bits.CKP = 0; // 0: idle state of clk=low
//    SSPCON1bits.SSPOV = 0; // Setting no overflow for slave
//    SSPCON1bits.SSPEN = 1;// Enabling Synchronous Serial Port Enable -
//    // NOTE: The above line requires the pins to be properly configured as input/output
//    
//    // Configuring SSPSTAT register
//    SSPSTATbits.SMP = //1 end, 0 middle
//    SSPSTATbits.CKE = 0; // which clock edge to transmit on
//    //SSPSTATbits.BF = 

typedef enum
{
  SPI_MASTER_OSC_DIV4  = 0b00100000,
  SPI_MASTER_OSC_DIV16 = 0b00100001,
  SPI_MASTER_OSC_DIV64 = 0b00100010,
  SPI_MASTER_TMR2      = 0b00100011,
  SPI_SLAVE_SS_EN      = 0b00100100,
  SPI_SLAVE_SS_DIS     = 0b00100101
}Spi_Type;

typedef enum
{
  SPI_DATA_SAMPLE_MIDDLE = 0b00000000,
  SPI_DATA_SAMPLE_END    = 0b10000000
}Spi_Data_Sample;

typedef enum
{
  SPI_CLOCK_IDLE_HIGH = 0b00001000,
  SPI_CLOCK_IDLE_LOW  = 0b00000000
}Spi_Clock_Idle;

typedef enum
{
  SPI_IDLE_2_ACTIVE = 0b00000000,
  SPI_ACTIVE_2_IDLE = 0b01000000
}Spi_Transmit_Edge;




void spiInit(Spi_Type sType, Spi_Data_Sample sDataSample, Spi_Clock_Idle sClockIdle, Spi_Transmit_Edge sTransmitEdge)
{
  TRISC5 = 0;
  if(sType & 0b00000100) //If Slave Mode
  {
    SSPSTAT = sTransmitEdge;
    TRISC3 = 1;
  }
  else //If Master Mode
  {
    SSPSTAT = sDataSample | sTransmitEdge;
    TRISC3 = 0;
  }
  SSPCON = sType | sClockIdle;
}

static void spiReceiveWait()
{
  while ( !SSPSTATbits.BF ); // Wait for Data Receipt complete
}

void spiWrite(char dat) //Write data to SPI bus
{
  SSPBUF = dat;
}

unsigned spiDataReady() //Check whether the data is ready to read
{
  if(SSPSTATbits.BF)
    return 1;
  else
    return 0;
}

char spiRead()    // Read the received data
{
  spiReceiveWait();      // Wait until all bits receive
  return(SSPBUF); // Read the received data from the buffer
}


// Note we are using PIC18F

// PIC16F877A Configuration Bit Settings
// 'C' source line config statements

// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.

// CONFIG
#pragma config FOSC = XT   // Oscillator Selection bits (XT oscillator)
#pragma config WDTE = OFF  // Watchdog Timer Enable bit (WDT disabled)
#pragma config PWRTE = OFF // Power-up Timer Enable bit (PWRT disabled)
#pragma config BOREN = OFF // Brown-out Reset Enable bit (BOR disabled)
#pragma config LVP = OFF   // Low-Voltage In-Circuit Serial Programming Enable bit
#pragma config CPD = OFF   // Data EEPROM Memory Code Protection bit
#pragma config WRT = OFF   // Flash Program Memory Write Enable bits
#pragma config CP = OFF    // Flash Program Memory Code Protection bit

#include <xc.h>
#include <pic16f877a.h>
#include "spi.h"

#define _XTAL_FREQ 8000000

void interrupt SPI_Slave_Read()
{
  if(SSPIF == 1)
  {
    PORTD = spiRead();
    spiWrite(PORTB);
    SSPIF = 0;
  }
}

void main()
{
  nRBPU = 0;    //Enable PORTB internal pull up resistor
  TRISB = 0xFF; //PORTB as input
  TRISD = 0x00; //PORTD as output
  PORTD = 0x00; //All LEDs OFF

  GIE = 1;
  PEIE = 1;
  SSPIF = 0;
  SSPIE = 1;
  ADCON1 = 0x07;
  TRISA5 = 1;

  spiInit(SPI_SLAVE_SS_EN, SPI_DATA_SAMPLE_MIDDLE, SPI_CLOCK_IDLE_LOW, SPI_IDLE_2_ACTIVE);

  while(1)
  {
    //Do something here
    __delay_ms(5);
  }
}
