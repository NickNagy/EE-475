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
#define _XTAL_FREQ 16000000UL
#define DESIRED_BR 9600
#define SPEC_DELAY_US 200
#pragma WDT = OFF
#pragma JTAG = OFF
//#pragma MCLR = ON

// measurement types
#define COMM_NO '0'
#define COMM_FREQ '1'
#define COMM_PRD '2'
#define COMM_TIME '3'
#define COMM_SPEC '4'
#define COMM_EVNT '5'
#define COMM_SPI '6'
#define COMM_SRAM '7'

#define N 256
#define Q3 PORTAbits.RA3
#define Q9 PORTAbits.RA2

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
unsigned long* magnitudes;//[N/2];
int imaginary[N] = {0};
int SRAM[2][16];
int counter = 0;
char SRAMdata = 0;
int singleSample;
int baud_rate;
//char mode;
char lineSkip[] = "\n";
int initTimerHigh = 0xFF;
int initTimerLow = 0xEB;
long long currTime = 0;

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

char getch(){
    while(PIR1bits.RCIF==0);
    char data = RCREG;
    return data;
}

void wait(){
    while(ADCON0bits.GO_nDONE);
}

int ADConversion(){
    ADCON0bits.GO_nDONE = 1;
	wait();
	return (ADRESH << 8) + ADRESL;
}

void putch(char value){
    while(PIR1bits.TXIF==0);
    TXREG = value;
}

void __interrupt() timerFull(){
    if (TMR0IF){
        TMR0H = initTimerHigh;
        TMR0L = initTimerLow;
        TMR0IF = 0; // clear interrupt flag
        currTime += 5; // about 5 micro-seconds to overflow
    }
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
    //COUNTER_RESET = 0;
    //PORTA = LATA;
    PORTAbits.RA1 = 0;
    __delay_ms(1);
}

void resetCounter() {
    //COUNTER_RESET = 1;
    //PORTA = LATA;
    PORTAbits.RA1 = 1;
    __delay_ms(1);
}

void updateAddress(){
    COUNTER_CLK = 1;
    PORTA = LATA;
    __delay_ms(500);
    COUNTER_CLK = 0;
    PORTA = LATA;
    __delay_ms(500);
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
    //__delay_ms(1);
    NOT_WE = 1;
    PORTE = LATE;
    //__delay_ms(1);
    updateAddress();
}

int getEvent(long long timeLimit){
    long long startTick = currTime;
    int numEvents = 0;
    while((numEvents <= 10000) && (currTime - startTick < timeLimit)){
        if(PORTAbits.AN4){
            numEvents++;
        }
    }
    return numEvents;
}

void writeToSpecAddress(char address, char data){
    TRISD = 0;
    NOT_OE = 1; // disable output
    PORTE = LATE;
    PORTD = data;
    //__delay_ms(1);
    goToAddress(address);
    NOT_WE = 0; // enable write
    PORTE = LATE;
    //__delay_ms(1);
    NOT_WE = 1; // disable write
    PORTE = LATE;
    //__delay_ms(1);
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
    //__delay_ms(1);
    goToAddress(address);
    NOT_OE = 0; // enable output
    PORTE = LATE;
    //__delay_ms(1);
    char data = PORTD;
    NOT_OE = 1; // disable output
    PORTE = LATE;
    //__delay_ms(1);
    updateAddress();
    return data;
}

void storeToSRAM(int measureType, int data){
    for (int i = 15; i > 1; i--){
        SRAM[i][0] = SRAM[i-1][0];
        SRAM[i][1] = SRAM[i-1][1];
    }
    SRAM[0][0] = measureType;
    SRAM[0][1] = data;
}

void printSRAM(){
    for (int i = 0; i < 16; i++){
        int measureType = SRAM[i][0];
        int data = SRAM[i][1];
        switch (measureType){
            case 1:
                printf("Frequency: %d Hz\n\r", data);
                break;
            case 2:
                printf("Period: %d microseconds\n\r", data);
                break;
            case 3:
                printf("Time: %d microseconds\n\r", data);
                break;
            case 5:
                printf("Event: %d events\n\r", data);
            default:
                printf("?\n\r");
        }
    }
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
        printf("Iteration: %d, Value: %d\n\r", j, SRAMdata);
    }
}

void testRXTX(){
    char result = getch();
    //__delay_ms(1);
    printf("%c\n\r", result);
    //putch(result);
    //__delay_ms(1);
}

void SPIWrite(char data){
    SSPBUF = data;
    //__delay_ms(1);
}

char SPIRead(){
    while(!SSPSTATbits.BF);
    //__delay_ms(1);
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
    TRISC5 = 0; // output (SDO)
    TRISC4 = 1; // input (SDI)
    TRISC3 = 0; // clock is an output
    setTRISB(0);
    SPIWrite(1);
    //setTRISB();
    char data = SPIRead();
    return data;
}

double getPeriod(){
    resetCounter();
    startCounter();
    long long firstTick = currTime;
    while(!PORTAbits.RA2){
        if(currTime - firstTick > 10000000){
            break;
        }
    }
    return (double)(currTime - firstTick);
}

double getFrequency(){
    double period = getPeriod();
    return 200000.0*(512.0/period);
}

void printSpectrum(){
    for (int i = 0; i < N; i++){
        samples[i] = ADConversion();
        __delay_us(SPEC_DELAY_US);
    }
    magnitudes = optfft(samples, imaginary);
    for (int j = 0; j < N/2; j++) {
        float freqCorrected = j*1000000.0/((float)N*(float)SPEC_DELAY_US);
        if(freqCorrected >= 500 && freqCorrected <= 1000){
            printf("Frequency: %.2f , Magnitude: %d\n\r", freqCorrected, magnitudes[j]);
        }
    }
}

void timerSetup(){
    TMR0H = initTimerHigh;
    TMR0L = initTimerLow;
    
    T0CONbits.T08BIT = 0; // 16-bit
    T0CONbits.PSA = 1; // bypasses prescalar
    T0CONbits.T0SE = 1;
    T0CONbits.T0CS = 0;
    INTCONbits.PEIE = 1;
    INTCONbits.TMR0IE = 1;
    INTCONbits.TMR0IF = 1;
    
    INTCON2bits.TMR0IP = 1;
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
    //SSPSTATbits.SMP = 0; // 0: middle, 1: end
    SSPSTATbits.CKE = 1; // which clock edge? (set opposite on slave)
    SSPSTATbits.SMP = 1; // disable slew rate
    TRISC7 = 1; // RX as input
    TRISC6 = 0; // TX as output
    TRISC5 = 0; // serial data out
    //TRISC4 = 0; // slave-select pin
    //TRISC3 = 1; // cleared for master 
    
    //TRISC = 0x80; 
    
    setTRISB(1); // PORT B as input

    TRISAbits.RA0 = 1;
    TRISAbits.RA1 = 0;
    TRISAbits.RA2 = 1;
    TRISAbits.RA3 = 1;
    TRISAbits.RA4 = 1;
    TRISE = 0x0;
    SPBRG = convert_baud_rate();
    
	// configuration for A/D converters
	ADCON0bits.CHS = 0b000;
    ADCON0bits.ADCS1 = 0;
    ADCON0bits.ADCS0 = 1;
	ADCON1bits.ADFM = 1; // 1 = right-justified, 0 = left-justified
	ADCON1bits.ADCS2 = 1;
	ADCON1bits.PCFG = 0b1110;
    
    printf("Welcome to Regal Entertainment.\n\r");
        
    timerSetup();
    
    char prevMode = 0;
    
    clearTX();
}

void main(void) {    
    init();
	while (1) {
        char mode = getch();
        switch(mode){
            case COMM_FREQ:
                initTimerHigh = 0xFF;               
                printf("Frequency: ");
                double freq = getFrequency();
                printf("%.2f Hz\n\r", freq);
                storeToSRAM(1, (int)freq);
                break;
            case COMM_PRD:                
                initTimerHigh = 0xFF;
                printf("Period: ");
                double period = getPeriod();
                printf("%.2f microseconds\n\r", period);
                storeToSRAM(2, (int)freq);
                break;
            case COMM_TIME:
                initTimerHigh = 0xFF;
                printf("Time: ");
                double time = getPeriod();
                printf("%.2f microseconds\n\r", time);
                storeToSRAM(3, (int)time);
                break;
            case COMM_SPEC:
                initTimerHigh = 0x00;
                printf("Beginning Spectrum Analysis...\n\r");
                printSpectrum();
                break;
            case COMM_EVNT:
                initTimerHigh = 0xFF;
                printf("Event: ");
                int events = getEvent(1000000);
                printf("%d events \n\r", events);
                storeToSRAM(5, events);
                break;
            case COMM_SPI:
                printf("SPI: ");
                printf("%d\n\r", testSPI());
            case COMM_SRAM:
                printf("Previous Measurements...\n\r");
                printSRAM();
                break;
            default:
                break;
        }
	}
	return;
}
