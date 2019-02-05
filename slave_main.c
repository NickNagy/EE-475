/*
 * File:   slave_main.c
 * Author: Nick Nagy
 *
 * Created on February 4, 2019, 3:23 PM
 */


#include <xc.h>
#include "spi.h"
#include "configvsmall.h"
#include "pic18f25k22.h"

void main(void) {
    
    SSPCON1bits.SSPM = 0b0100;
    SSPCON1bits.CKP = 0; // 0: idle state of clk=low
    SSPSTATbits.CKE = 0; // which clock edge to transmit on 
    TRISC3 = 1;
    
    while() {
        
    }
}
