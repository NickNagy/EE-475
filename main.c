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
#include "constants.h"
#include "optfft.h"

// temporarily keeping local, b/c not recognized when stored in constants.h:
#define _XTAL_FREQ 4000000
#define DESIRED_BR 9600
#pragma WDT = OFF
#define COMM_FREQ 1

// globals, helps free up space by putting samples om the heap
int samples[256];

unsigned int convert_baud_rate() {
	unsigned char factor;
	if (BRGH) {
		factor = 16;
	}
	else {
		factor = 64;
	}
	return (int)(_XTAL_FREQ / (factor*(DESIRED_BR)) - 1);
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

	// spec page 170
	SYNC = 0;
	BRGH = 1;

    unsigned char counter = 0;

	// http://www.microcontrollerboard.com/pic_serial_communication.html
	SPBRG = convert_baud_rate();
					   
	TRISB = 0;
	PORTB = 0;
	// TXSTA = 0b00100010; // determining settings for the transmitter
	// RCSTA = 0b10010000; // determining settings for the receiver
	SSPSTATbits.SMP = 1; // disable slew rate

	// configuration for A/D converters
	ADCON0bits.CHS = 0b000;
	ADCON1bits.ADFM = 1; // 1 = right-justified, 0 = left-justified
	ADCON1bits.ADCS2 = 1;
	ADCON1bits.PCFG = 0b1001;

	clearTX();
    int imaginary[256] = {0}; // for FFT

	while (1) {
		clearRX(); // should RX send nothing b/w measurements??
		if (TXREG != 0) {
			while (ADCON0bits.GO_NOT_DONE); // wait til done reading
			int singleSample = (ADRESH << 8) + ADRESL;
            if (TXREG == COMM_FREQ) {
                samples[counter] = singleSample;
                if (counter == 255) {
                    clearTX();
                    writeRX(optfft(samples, imaginary));
                }
                counter = (counter + 1) % 255;
            } else {
                writeRX(singleSample);
            }
		}
		__delay_ms(1);
	}
	return;
}
