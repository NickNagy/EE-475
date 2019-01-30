/*
 * File:   main.c
 * Author: Nick Nagy
 *
 * Created on January 26, 2019, 2:54 PM
 */

#include <xc.h>
//#include "config.h"
//#include "pic18.h"
//#include "pic18f452.h"
#include "configv16.h"
#include "pic16f877a.h"
#include "stdio.h"
#include "constants.h"
#include "optfft.h"

// temporarily keeping local, b/c not recognized when stored in constants.h:
#define _XTAL_FREQ 4000000
#define DESIRED_BR 9600
#pragma WDT = OFF
#pragma JTAG = OFF
#define COMM_FREQ 1
#define N 32

// globals, helps free up space by putting samples om the heap
int samples[N];
int imaginary[N] = {0};
int counter = 0;
int singleSample;
int baud_rate;

// for debugging purposes
#define MODE 0
int RXResult;

unsigned int convert_baud_rate() {
	unsigned long factor;
	if (TXSTAbits.BRGH) {
		factor = 16;
	}
	else {
		factor = 64;
	}
	return (unsigned int)((unsigned long)_XTAL_FREQ / (factor*(DESIRED_BR)) - 1);
}

// might be a nonsensical function
char getRX(){
    while(PIR1bits.RCIF==0);
    RCIF = 0;
    return RCREG;
}

void writeTX(char value){
    while(TXIF==0);
    //TXIF = 0;
    TXREG = value;
}

void clearTX() {
	writeTX(0);
}

void main(void) {    
    
    TXSTAbits.SYNC = 0; // 0 = asynchronous
    TXSTAbits.BRGH = 1; // used for baud rate calculation
    TXSTAbits.TX9 = 0;
    TXSTAbits.TXEN = 1; // enable transmit
    RCSTAbits.RX9 = 0;
    RCSTAbits.SPEN = 1; // enable RX and TX as serial
    RCSTAbits.CREN = 1; // continuous receive

	// http://www.microcontrollerboard.com/pic_serial_communication.html
	TRISC = 0x80;
    baud_rate = convert_baud_rate();
    SPBRG = baud_rate;
					   
	TRISB = 0;
	PORTB = 0;
	SSPSTATbits.SMP = 1; // disable slew rate

	// configuration for A/D converters
	ADCON0bits.CHS = 0b000;
    ADCON0bits.ADCS1 = 0;
    ADCON0bits.ADCS0 = 1;
	ADCON1bits.ADFM = 1; // 1 = right-justified, 0 = left-justified
	ADCON1bits.ADCS2 = 1;
	ADCON1bits.PCFG = 0b1111;

	//clearRX();

	while (1) {
		clearTX(); // should TX send nothing b/w measurements??
		char i;
        char a[] = {"Testing...\n\r"};
        for (i = 0; a[i]!=0; i++) {
            writeTX(a[i]);
        }
        if (MODE != 0) {
            ADCON0bits.GO_nDONE = 1;
			while (ADCON0bits.GO_nDONE); // wait til done reading
			singleSample = (ADRESH << 8) + ADRESL;
            if (MODE == COMM_FREQ) {
                //singleSample = (ADRESH << 8) + ADRESL;
                samples[counter] = singleSample;//(ADRESH << 8) + ADRESL;
                if (counter == (N-1)) {
                    //clearTX();
                    int frequency = optfft(samples, imaginary);
                    float period = 1.0/frequency;
                    writeTX((char)frequency);
                }
                counter = (counter + 1) % N;
            }
        }
		__delay_ms(500);
	}
	return;
}
