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
//#include "config16.h"
//#include "pic16f877a.h"
#include "stdio.h"
#include "constants.h"
#include "optfft.h"
//#include "spi.h"

// temporarily keeping local, b/c not recognized when stored in constants.h:
#define _XTAL_FREQ 4000000UL
#define DESIRED_BR 9600
#pragma WDT = OFF
#pragma JTAG = OFF
//#pragma MCLR = ON
#define COMM_FREQ 1
#define COMM_SPEC 4
#define N 256

union {
    unsigned char all; // since technically not a byte
    struct {
        unsigned R0: 1;
        unsigned R1: 1;
        unsigned R2: 1;        
    } bits;
} tempEPort;

union {
    unsigned char all;
    struct {
        unsigned R0: 1;
        unsigned R1: 1;
        unsigned R2: 1;
        unsigned R3: 1;
        unsigned R4: 1;
        unsigned R5: 1;
    } bits;
} tempAPort;

// define pins
#define NOT_OE LATE0
#define NOT_WE LATE1
#define COUNTER_RESET LATA1
#define COUNTER_CLK LATA2

// globals, helps free up space by putting samples om the heap
int samples[N];
int imaginary[N] = {0};
int counter = 0;
char SRAMdata = 0;
int singleSample;
int baud_rate;
char mode;
char lineSkip[] = "\n";

// for debugging purposes
#define MODE 0

unsigned int convert_baud_rate() {
	unsigned long factor;
	if (TXSTAbits.BRGH) {
		factor = 16;
        SSPCON1bits.SSPM = 0b0001;
	}
	else {
		factor = 64;
        SSPCON1bits.SSPM = 0b0010;
	}
	return _XTAL_FREQ / (factor*(DESIRED_BR)) - 1;
}

char getRX(){
    while(PIR1bits.RCIF==0);
    char data = RCREG;
    return data;
}

void wait(){
    while(ADCON0bits.GO_nDONE);
}

void putch(char value){
    while(PIR1bits.TXIF==0);
    TXREG = value;
}

void writeVal(char val) {
    putch(val);
    putch(lineSkip[0]);
    putch(lineSkip[1]);
}

void writeLine(char line[]){
    for (char i = 0; line[i]!= 0; i++){
        putch(line[i]);
    }
    putch(lineSkip[0]);
    putch(lineSkip[1]);
}

void clearTX() {
	putch(0);
}

void startCounter() {
    COUNTER_RESET = 0;
    PORTA = LATA;
    __delay_ms(1);
}

void resetCounter() {
    COUNTER_RESET = 1;
    PORTA = LATA;
    __delay_ms(1);
}

void updateAddress(){
    COUNTER_CLK = 1;
    PORTA = LATA;
    __delay_ms(1);
    COUNTER_CLK = 0;
    PORTA = LATA;
    __delay_ms(1);
}

void goToAddress(char address) {
    resetCounter();
    startCounter();
    for (char i = 0; i < address; i++) {
        updateAddress();
    }
}

void writeToCurrAddress(char data){
    TRISD = 0;
    NOT_OE = 1; // disable output
    PORTE = LATE;
    PORTD = data;
    __delay_ms(1);
    NOT_WE = 0;
    PORTE = LATE;
    __delay_ms(1);
    NOT_WE = 1;
    PORTE = LATE;
    __delay_ms(1);
    updateAddress();
}

void writeToSpecAddress(char address, char data){
    TRISD = 0;
    NOT_OE = 1; // disable output
    PORTE = LATE;
    PORTD = data;
    __delay_ms(1);
    goToAddress(address);
    NOT_WE = 0; // enable write
    PORTE = LATE;
    __delay_ms(1);
    NOT_WE = 1; // disable write
    PORTE = LATE;
    __delay_ms(1);
    updateAddress();
}

char readFromCurrAddress(){
    TRISD = 1; 
    NOT_WE = 1;
    NOT_OE = 0;
    PORTE = LATE;
    __delay_ms(1);
    char data = PORTD;
    NOT_OE = 1;
    PORTE = LATE;
    __delay_ms(1);
    updateAddress();
    return data;
}

char readFromSpecAddress(char address){
    TRISD = 1;
    NOT_OE = 1; // disable output
    NOT_WE = 1; // disable write
    PORTE = LATE;
    __delay_ms(1);
    goToAddress(address);
    NOT_OE = 0; // enable output
    PORTE = LATE;
    __delay_ms(1);
    char data = PORTD;
    NOT_OE = 1; // disable output
    PORTE = LATE;
    __delay_ms(1);
    updateAddress();
    return data;
}

void testRAM(){
    resetCounter();
    startCounter();
    for (char i = 0; i < 32; i++) {
        writeToCurrAddress(i);
    }
    resetCounter();
    startCounter();
    for (char j = 0; j < 32; j++) {
        SRAMdata = readFromCurrAddress();
    }
}

void testRXTX(){
    char result = getRX();
    __delay_ms(1);
    writeVal(result);
    __delay_ms(1);
}

void SPIWrite(char data){
    SSPBUF = data;
    __delay_ms(1);
}

char SPIRead(){
    while(!SSPSTATbits.BF);
    __delay_ms(1);
    return SSPBUF;
}

void setTRISB(char val){
    TRISBbits.RB0 = val;
    TRISBbits.RB1 = val;
    TRISBbits.RB2 = val;
    TRISBbits.RB3 = val;
    TRISBbits.RB4 = val;
    TRISBbits.RB5 = val;
    __delay_ms(1);
}

char testSPI(){
    setTRISB(0);
    SPIWrite(1);
    //setTRISB();
    char data = SPIRead();
    return data;
}

void init(){
    nRBPU = 0; // PORTB pull-up resistors
        
    INTCON1bits.GIE = 1; // global interrupt
    
    TXSTAbits.SYNC = 0; // 0 = asynchronous
    TXSTAbits.BRGH = 1; // used for baud rate calculation
    TXSTAbits.TX9 = 0;
    TXSTAbits.TXEN = 1; // enable transmit
    RCSTAbits.RX9 = 0;
    RCSTAbits.SPEN = 1; // enable RX and TX as serial
    RCSTAbits.CREN = 1; // continuous receive
    // ?
    RCSTAbits.ADDEN = 1;
    RCSTAbits.FERR = 0;
    RCSTAbits.OERR = 0;

    // SPI and serial stuff
    SSPCON1bits.CKP = 0; // 0: idle clk state = low level
    SSPSTATbits.SMP = 0; // 0: middle, 1: end
    SSPSTATbits.CKE = 1; // which clock edge? (set opposite on slave)
    SSPSTATbits.SMP = 1; // disable slew rate
    /*TRISC7 = 1; // RX as input
    TRISC6 = 0; // TX as output
    TRISC5 = 0; // serial data out
    TRISC4 = 0; // slave-select pin
    TRISC3 = 0; // cleared for master 
    */
    TRISC = 0x80; 
    
    setTRISB(1); // PORT B as input

    TRISAbits.RA0 = 1;
    TRISAbits.RA1 = 0;
    TRISAbits.RA2 = 0;
    TRISE = 0x0;
    SPBRG = convert_baud_rate();
    
	// configuration for A/D converters
	ADCON0bits.CHS = 0b000;
    ADCON0bits.ADCS1 = 0;
    ADCON0bits.ADCS0 = 1;
	ADCON1bits.ADFM = 1; // 1 = right-justified, 0 = left-justified
	ADCON1bits.ADCS2 = 1;
	ADCON1bits.PCFG = 0b1110;
    
    clearTX();
}

void main(void) {    
    init();
	while (1) {
        //resetCounter();
        //testRAM();
        //testRXTX();
        printf("Hello world!\n\r");
        //__delay_ms(1);
        //putchar(97);
        //__delay_ms(500);
        //writeLine("Hello, World!");
        /*ADCON0bits.GO_nDONE = 1;
        while(ADCON0bits.GO_nDONE);
        if (mode != COMM_FREQ && mode != COMM_SPEC) {
            writeToAddress(ADRESL);
            writeToAddress(ADRESH);
        }
		clearTX(); // should TX send nothing b/w measurements??
        mode = getRX();
        if (mode > 0) {
            ADCON0bits.GO_nDONE = 1;
			while (ADCON0bits.GO_nDONE); // wait til done reading
			singleSample = (ADRESH << 8) + ADRESL;
            if (mode == COMM_FREQ) {
                samples[counter] = singleSample;
                if (counter == (N-1)) {
                    int frequency = optfft(samples, imaginary);
                    writeVal((char)frequency);
                }
                counter = (counter + 1) % N;
            } else {
                writeVal((char)singleSample);
            }
        }
		__delay_ms(5);*/
	}
	return;
}
