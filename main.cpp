/*=============================================================================
Copyright University of Essex 2017
Author: Kuncheng Li

FILE - main.c
    mbed LPC1768 application.

DESCRIPTION
    alarm 1 laboratory solution.
    hardware: mbed LPC1768, an extension board.
    Use a terminal program such as 'HyperTerminal' to communicate with the 
    application.
    The serial port configuration is shown below.
        9600 Baud
        8 data bits
        No parity bits
        One stop bit
        No hardware flow control
==============================================================================*/

/******************************************************************************
Include head files.
******************************************************************************/
#include "mbed.h"
#include "TextLCD.h"
// TextLCD
TextLCD lcd(p15, p16, p17, p18, p19, p20);//, TextLCD::LCD20x4); // rs, e, d4-d7
// Read from switches and keypad
BusOut rows(p26,p25,p24);
BusIn cols(p14,p13,p12,p11);
// Control external LEDs
SPI sw(p5, p6, p7);
DigitalOut cs(p8);
// Serial USB
Serial pc(USBTX, USBRX); // tx, rx
// Temperature reading
I2C i2c(p9, p10);              // I2C: SDA, SCL
//set led1 as alarm
DigitalOut Sounder(LED1);
DigitalOut led4(LED4);
/******************************************************************************
Declaration of functions.
******************************************************************************/
//define functions
void alarmConfig(void);
void alarm_state();

int  read_switch(void);
void  switchleds();
int getSwitch();
void initleds();
void setleds(int ledall);
void setled(int ledno, int ledstate);

char getKey();
void setKey(void);
int  testCode(void);

void sounder_blink();
void pattern(void);
void patternoff(void);
void Sounderoff(void);

void system_alarm(void);
void system_sounder(void);
void system_set(void);

/******************************************************************************
Global variables.
******************************************************************************/
//set states
enum State {unset, exits, set, entry, alarm, report} state;
//set key table
char Keytable[] = { 'F', 'E', 'D', 'C',
                    '3', '6', '9', 'B',
                    '2', '5', '8', '0',
                    '1', '4', '7', 'A'
                  };
char keyCode[] = {'1','2','3','4'};
//define two variables store key input
char b;
char c;
//use for debonece the key of pinpad
char code[4];
int  fail = 0; // number of failed attempts
int  success;  // 0~4: number of successful matched keycodes; 5 indicates switch 
               //changing; 6 indicates time expired
int  zone;     //set zone number for full set zone and entry/exit zone
//define display 0 means have not display, 1 means info has displayed
int display = 0; 
int flag ;     //define flag for states
int sensorOn = 0; //define sensor on to show if sensors has been activated
int  led_bits = 0;   // global LED status used for readback
//define timers
Ticker timer,timersw;
Timeout t_alarm, t_entry, t_exit;

/*=============================================================================

FILE - main.cpp

DESCRIPTION
    Initiates the Finite State Machine
=============================================================================*/
int main()
{

    alarmConfig();//initialize leds and switches
    //initialize lcd screen
    lcd.cls();
    lcd.locate(2,0);
    lcd.printf("Alarm Lab");
    pc.printf("\n\n\r              ALARM LAB\n\r (c)Copyright University of Essex 2017 \n\r            Author: Kuncheng Li\n\r");
    //set default key position to '_'
    setKey();
    //call switchleds functin per 0.1 second
    timer.attach(&switchleds,0.1);
    //loop alarm_state function
    while (1) {
        alarm_state();  // FSM routine
    }
}

/**********************************************************************************
Finite State Machine for Alarm
**********************************************************************************/
void alarm_state()
{
    switch(state) {
            /*--------------------------------------------------------------------------------
               UN_SET STATE (STATE 1)
                   un_set led enabled
                   Internal sounder disabledabled
                   Sensors not monitored.
            ---------------------------------------------------------------------------------*/
        case unset:
            flag = 8; //set flag to 8
            led_bits  = 0x0000;  // set the external leds to off
            sw.write(led_bits); //turn off all leds
            cs = 1;
            cs = 0;
            timersw.detach(); //reset timer
            patternoff();   //reset led1
            display = 0;    //reset display
            pc.printf("\n\r Unset mode\n\r");
            lcd.cls();
            lcd.printf("Unset mode");

            setled(8,3);  // turn unset led on
            success = testCode();
            if (success == 4) {
                fail = 0;  // failure counter reset
                state = exits;
                setled(8,0);

            } else if (fail == 2) {
                pc.printf("\n\r attemp %d", fail+1);
                state = alarm;
                setled(8,0);
                //flag = 4;
                zone = 5;    // zone identifier(5 represents an invalid code is entered three times)
                fail = 0;      //failure counter reset

            } else {
                fail++;
                state = unset;
                pc.printf("\n\r attemp %d", fail);
            }

            break;

            /*--------------------------------------------------------------------------------
                EXIT STATE (STATE 2)
                    un_set led flashes
                    Internal sounder enabled for 250msec every 500msec.
            ---------------------------------------------------------------------------------*/
        case exits:
            flag = 7;
            setled(7,3);   // turn exits led on
            pattern();     // Sounder switches on and then off at 250ms intervals
            system_set();  // call system_set function

            pc.printf("\n\r Exit mode\n\r");
            lcd.cls();
            lcd.printf("Exit mode");

            success = testCode();
            //if sensor is inactivated, test code, else,
            // break and move to another state
            if(sensorOn == 0) {
                if (flag == 7 && success == 4) {
                    fail = 0;  // failure counter reset
                    setled(7,0);// turn off led 7
                    state = unset;// set state to unset
                    t_exit.detach();// detach timer
                    flag = 8; //set flag to 8


                } else if( flag == 7 && fail == 2) {
                    pc.printf("\n\r attemp %d", fail+1);
                    timersw.detach();// detach timer
                    t_exit.detach();// detach timer
                    state = alarm;// set state to alarm
                    setled(7,0);// turn off led 7
                    zone = 5;    // zone identifier(5 represents an invalid code is entered three times)
                    fail = 0;      //failure counter reset


                } else if(flag == 7 && fail<2  ) {
                    fail++;
                    state = exits;
                    pc.printf("\n\r attemp %d", fail);
                }
            }

            else {
                break;
            }

            break;

            /*--------------------------------------------------------------------------------
               SET STATE (STATE 3)
                   set led enabled
                   Internal sounder disabled.
            ---------------------------------------------------------------------------------*/
        case set:
            flag = 6;// set flag to 6
            setled(7,0);// turn off led 7
            setled(6,3);   // turn set led on
            patternoff();     // Sounder switches on and then off at 250ms intervals
            //if info has been displayed, don't display it again
            if (display == 0) {
                pc.printf("\n\r Set mode\n\r");
                lcd.cls();
                lcd.printf("Set mode");
                display = 1;
            }
            //get switches value
            int switches;
            switches = getSwitch();
            //if open the second switch(from right to left),
            //change state to alarm mode
            int i = 1;
            if ((switches & 0x0001<<i)!=0) {
                switchleds();
                state = alarm;
                zone = 2;    // zone identifier(2 represents fullset)

            }
            //if open thethe first switch, change to entry mode
            i = 0;
            if ((switches & 0x0001<<i)!=0) {
                switchleds();
                state = entry;
            }


            break;

            /*--------------------------------------------------------------------------------
                ENTRY STATE (STATE 4)
                    un_set led flashes
                    Internal sounder enabled for 250ms every 500ms.
            ---------------------------------------------------------------------------------*/
        case entry:
            flag = 5;// set flag to 5
            setled(5,3);   // turn entry led on
            pattern();     // Sounder switches on and then off at 250ms intervals
            zone = 3;
            pc.printf("\n\r Entry mode\n\r");
            lcd.cls();
            lcd.printf("Entry mode");
            system_alarm();

            success = testCode();
            if(sensorOn == 0) {
                if (success == 4) {
                    setled(5,0);
                    state = unset;
                    t_entry.detach();
                    flag = 8;
                } else if(flag == 5) {
                    state = entry;
                    pc.printf("\n\r attemp %d", fail);
                }
            }

            else {
                break;
            }

            break;
            /*--------------------------------------------------------------------------------
                ALARM STATE (STATE 5)
                    alarm led enabled
                    Internal and External sounders enabled.
            ---------------------------------------------------------------------------------*/
        case alarm:
            sensorOn = 0;//reset sensorOn
            flag = 4;
            setled(5,0);//turn off led 5
            setled(4,3);//turn on led 4
            patternoff();
            Sounder = 1;
            t_alarm.attach(&Sounderoff, 10.0);// turn off the sounder after 10 seconds

            pc.printf("\n\r Alarm mode\n\r");
            lcd.cls();
            lcd.printf("Alarm mode");
            success = testCode();

            if (success == 4) {
                state = report;
                setled(4,0);
                t_alarm.detach();
                flag = 3;
            }
            break;
            /*--------------------------------------------------------------------------------
                REPORT (STATE 6)
                    un-set and alarm leds enabled
                    Internal sounder remains enabled.
                    External sounder enabled.
            ---------------------------------------------------------------------------------*/
        case report:
            flag = 3; //set flag to 3
            setled(3,3);   // turn entry led on

            pc.printf("\n\r Report mode\n\r");
            lcd.cls();
            lcd.printf("Zone numbers:%i",zone);
            lcd.locate(0,1);
            lcd.printf("C key to clear");
            //wait for key C to be pressed
            while (1) {
                char b = getKey();
                if (b == 'C') {
                    state = unset;
                    alarmConfig();
                    break;
                }
            }
            break;
    } // end switch(state)

} // end alarm_state()
/*
 function used to read switch value
*/
void readSwitch (void)
{
    int switches;
    switches = getSwitch();
    //if in exit or entry mode, and one switch has been activated
    if (flag == 7 && (switches & 0x0001<<1)!=0 || flag == 5 && (switches & 0x0001<<1)!=0) {
        if(flag == 7) {
            setled(7,0);
            t_exit.detach();
        } else {
            setled(5,0);
            t_entry.detach();
        }
        //set led on and set sensorOn to 1
        switchleds();
        sensorOn = 1;
        //change state to alarm
        patternoff();
        state = alarm;
        zone = 2;
        timersw.detach();
    }
}
/**********************************************************************************
Configurations
**********************************************************************************/
void alarmConfig()
{
    cs=0;
    sw.format(16,0);
    sw.frequency(1000000);
    state = unset;   // Initial state

    led_bits  = 0x0000;  // turn off all the external leds
    sw.write(led_bits);
    cs = 1;
    cs = 0;
}

/**********************************************************************************
External switches
**********************************************************************************/
/*
 function used to get value of switches
*/
int getSwitch()
{
    int switches;
    rows = 4;
    switches = cols;
    rows = 5;
    switches = switches*16 + cols;
    return switches;
}
void switchleds()
{
    int switches;
    switches = getSwitch();
    for(int i=0; i<=7; i++) {
        if ((switches & 0x0001<<i)!=0) {                        // 1, then turn on
            led_bits  = led_bits | (0x0003 << i*2);
        } else {                                                // 0, then turn off
            led_bits  = led_bits & ((0x0003 << i*2) ^ 0xffff);
        }
    }
    sw.write(led_bits);
    cs = 1;
    cs = 0;

    //return switches;
}

/**********************************************************************************
External LED functionality
**********************************************************************************/
void initleds()
{
    cs = 0;                                        // latch must start low
    sw.format(16,0);                               // SPI 16 bit data, low state, high going clock
    sw.frequency(1000000);                         // 1MHz clock rate
}

void setleds(int ledall)
{
    led_bits = ledall;                              // update global LED status
    sw.write((led_bits & 0x03ff) | ((led_bits & 0xa800) >> 1) | ((led_bits & 0x5400) << 1));
    cs = 1;                                        // latch pulse start
    cs = 0;                                        // latch pulse end
}

void setled(int ledno, int ledstate)
{
    ledno = 9 - ledno;
    ledno = ((ledno - 1) & 0x0007) + 1;             // limit led number
    ledno = (8 - ledno) * 2;                        // offset of led state in 'led_bits'
    ledstate = ledstate & 0x0003;                   // limit led state
    ledstate = ledstate << ledno;
    int statemask = ((0x0003 << ledno) ^ 0xffff);   // mask used to clear led state
    led_bits = ((led_bits & statemask) | ledstate); // clear and set led state
    setleds(led_bits);
}

/**********************************************************************************
Keypad functionality
**********************************************************************************/
char getKey()
{
    int i,j;
    char ch=' ';

    for (i = 0; i <= 3; i++) {
        rows = i;
        for (j = 0; j <= 3; j++) {
            if (((cols ^ 0x00FF)  & (0x0001<<j)) != 0) {
                ch = Keytable[(i * 4) + j];
            }
        }
    }
    wait(0.2); //debouncing
    return ch;
}

int testCode(void)
{
    int a, y;
    char b;
    lcd.locate(0, 1);
    lcd.printf("Enter Code: ____");
    y = 0;
    timersw.attach(&readSwitch,0.1);

    for(a = 0; a < 4; a++) {
        // if sensor on, or in set and report mode, break the loop
        if(sensorOn == 1 || flag ==6 || flag == 3) {
            break;
        } else {
            b = getKey();
            switch(b) {
                case ' ':
                    a--;
                    break;
                case 'C':   // use 'C' to delete input
                    if (a > 0) {
                        a = a-2;
                        lcd.locate(13+a, 1);
                        lcd.putc('_');
                        if ( code[a+1] == keyCode[a+1]) {
                            y--;
                        }
                    } else if (a == 0) {
                        a--;
                    }
                    break;
                default:
                    code[a] = b;
                    lcd.locate(12+a, 1);
                    lcd.putc('*');
                    if(code[a] == keyCode[a]) {
                        y++;
                    }
            }
        }
    }
    //if no sensor has been activated and not in set
    //or report mode, display and wait for button B
    if(sensorOn !=1 && flag !=6 && flag !=3) {
        lcd.cls();
        lcd.locate(0,1);
        lcd.printf("Press B to set");
    }
    //wait for button B to be pressed
    while (1) {

        if(sensorOn == 1 || flag ==6 || flag == 3) {
            break;
        } else {
            b = getKey();
            if (b == 'B')
                break;
        }
    }

    return(y);
}
/*
 function used to reset input keys to '_'
*/
void setKey(void)
{
    int a;
    char b;
    lcd.locate(0, 1);
    lcd.printf("Init  Code: ____");
    for(a = 0; a < 4; a++) {
        b = getKey();

        switch(b) {
            case ' ':
                a--;
                break;
            case 'C':
                if (a > 0) {
                    a = a-2;
                    lcd.locate(13+a, 1);
                    lcd.putc('_');
                } else if (a == 0) {
                    a--;
                }
                break;
            default:
                lcd.locate(12+a, 1);
                lcd.putc(b);
                keyCode[a] = b;
        }
    }
    wait(1);

}

/**********************************************************************************
Simulation of alarm  internal sounder
**********************************************************************************/
void sounder_blink()
{
    Sounder = !Sounder;
}

void pattern(void)
{
    timer.attach(&sounder_blink, 0.25);
}

void patternoff(void)
{
    timer.detach();  // turn the Sounder off
    Sounder = 0;
}

void Sounderoff(void)
{
    Sounder = 0;
}

/**********************************************************************************
Set system state
**********************************************************************************/
void system_alarm(void)
{
    //after 2 minutes, call alarm_state function 
    //and change state to alarm, than detach timer
    t_entry.attach(&alarm_state,120.0);
    state = alarm;
    timersw.detach();
}
void system_sounder(void)
{
    //after two minutes, call Soundoff function
    //to turn off the led
    t_alarm.attach(&Sounderoff, 120.0);
}
void system_set(void)
{
    //after one minute, call alarm_state
    //function, and set state to set mode
    t_exit.attach(&alarm_state, 60.0);
    state = set;
    timersw.detach();
}
