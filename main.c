/*
 * File:   main.c
 * Author: Nick Nagy
 *
 * Created on January 26, 2019, 2:54 PM
 */


#include <xc.h>
#include "config.h"
#include "pic18.h"
#include "pic18f452.h"
#include "stdio.h"

#define _XTAL_FREQ 4000000
#pragma config WDT=OFF
#define DESIRED_BR 9600

// __delay_ms
// TRISD1: 0 for output 1 for input
// RD1: 
// TODO: TX-RX connection to Mega

// resolution = sample_rate/N_samples

void main(void) {
    
    // spec page 170
    SYNC = 0;
    BRGH = 1;
    
    unsigned int baud_rate = convert_baud_rate();
    
    // http://www.microcontrollerboard.com/pic_serial_communication.html
    TRISB = 0;
    PORTB = 0;
    // TXSTA = 0b00100010; // determining settings for the transmitter
    // RCSTA = 0b10010000; // determining settings for the receiver
    TXREG = 0x0;
    SSPSTAT[7] = 1; // disable slew rate
    
    // may need to convert to binary representation?
    SPBRG = baud_rate; // convert_baud_rate();
    // SSPADD = 9600;
    while (1) {
        TXREG++;
        while(!TRMT);
        while(!RCIF);
        PORTB=RCREG; 
        __delay_ms(1);
    }
    return;
}

unsigned int convert_baud_rate(){
    unsigned char factor;
    if (BRGH){
        factor = 16;
    } else {
        factor = 64;
    }
    return int(_XTAL_FREQ/(factor*(DESIRED_BR))-1);
}
