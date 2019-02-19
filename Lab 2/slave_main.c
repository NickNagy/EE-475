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

void main(void) {
    
    // Configuring SSPCON register
    SSPCON1bits.SSPM = 0b0100; //0100 = SPI Slave mode, clock = SCK pin, SS pin control enabled
    SSPCON1bits.CKP = 0; // 0: idle state of clk=low
    SSPCON1bits.SSPOV = 0; // Setting no overflow for slave
    SSPCON1bits.SSPEN = 1;// Enabling Synchronous Serial Port Enable -
    // NOTE: The above line requires the pins to be properly configured as input/output
    
    // Configuring SSPSTAT register
    SSPSTATbits.SMP = //1 end, 0 middle
    SSPSTATbits.CKE = 0; // which clock edge to transmit on
    //SSPSTATbits.BF = 
    
    
    // set i/o
    TRISC3 = 1;
    
    // taking measurement
    while(1) {     
        SSPCON1bits.WCOL = 0; // No collision exists, The SSPBUF register is now ready to be overwritten
        
        // load SSPBUF with data to send  
        SSPBUF1.
        
        
    }
}

