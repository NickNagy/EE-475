/*
 * File:   slave_main.c
 * Author: Nick Nagy, Nick Orlov
 *
 * Created on February 4, 2019, 3:23 PM
 */


// PIC16F877A Configuration Bit Settings
// 'C' source line config statements

// #pragma config statements should precede project file includes.
// Use project enums instead of #define for ON and OFF.

#include <xc.h>
#include <pic18f25k22.h>
#include "slave_config.h"
//#include "spi.h"

#define _XTAL_FREQ 16000000UL

char readSPI(){
    while(!SSPSTATbits.BF);
    return (SSPBUF);
}

void writeSPI(char data){
    TRISC = 0x00; // set PORTC as output
    SSPBUF = data;
}

void __interrupt() SPI_Slave_Read()
{
  if(SSPIF == 1)
  {
    TRISC = 0xFF; // set as input
    char data = readSPI();
    writeSPI(data);
    SSPIF = 0;
  }
}

void main()
{
  //nRBPU = 0;    //Enable PORTB internal pull up resistor
  PORTC = 0xFF; 
  GIE = 1;
  PEIE = 1;
  SSPIF = 0;
  SSPIE = 1;
  ADCON1 = 0x07;
  //TRISA5 = 1;
  
  SSP2CON1bits.CKP = 0;
  SSPSTATbits.CKE = 0;
  SSPSTATbits.SMP = 1; // disable slew rate

  while(1)
  {
    __delay_ms(1);
  }
}
