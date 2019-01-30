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

void writeRX(int value){
    RCREG = value;
}

void writeTX(int value){
    TXREG = value;
}

void clearRX() {
	writeRX(0);
}

void clearTX() {
	writeTX(0);
}

void main(void) {    
    
    TXSTAbits.SYNC = 0; // 0 = asynchronous
    TXSTAbits.BRGH = 1; // used for baud rate calculation
    RCSTAbits.SPEN = 1; // enable RX and TX as serial
    RCSTAbits.CREN = 1; // continuous receive

	// http://www.microcontrollerboard.com/pic_serial_communication.html
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
    writeRX(1);

	while (1) {
		clearTX(); // should TX send nothing b/w measurements??
		if (RCREG != 0) {
            ADCON0bits.GO_nDONE = 1;
			while (ADCON0bits.GO_nDONE); // wait til done reading
			singleSample = (ADRESH << 8) + ADRESL;
            if (RCREG == COMM_FREQ) {
                singleSample = (ADRESH << 8) + ADRESL;
                samples[counter] = singleSample;//(ADRESH << 8) + ADRESL;
                if (counter == (N-1)) {
                    clearTX();
                    int frequency = optfft(samples, imaginary);
                    writeTX(frequency);
                }
                counter = (counter + 1) % N;
            } else {
                writeTX(1);
            }
		} else {
            writeTX(1);
        }
		__delay_ms(1);
	}
	return;
}
