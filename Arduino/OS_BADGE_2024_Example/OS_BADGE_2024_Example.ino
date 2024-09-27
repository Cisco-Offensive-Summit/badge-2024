//DEMO Sketch for OS2024 Badge to simultaneously demonstrate all peripherals (Orange LED, TFT + backlight control, EPD, Neopixel, Buttons)

//Include files                     // electronic paper display (EPD) ports: EPD_MISO=9, EPD_MOSI=11, EPD_CLK=12, EPD_CS=18
#include <EPD_V231_G2.h>            // you MUST modify the call in the SPI_on function in EPD_V231_G2.cpp to be SPI.begin(EPD_CLK, EPD_MISO, EPD_MOSI, EPD_CS);         
#include <epd_images.h>             // header file with a cat 200x96 EPD image array, "JED!!" 200x96 EPD image array, and a custom 200x96 OS224 EPD image array
#include <Adafruit_ST7735.h>        // Hardware-specific library for ST7735 TFT displays 
#include <Adafruit_NeoPixel.h>      // Neopixel drivery for addressable LED's D3, D4, D5, D6

// button ports on OS2024 Badge 
#define S4 17
#define S5 16
#define S6 15
#define S7 7

// Neopixel ports for OS2024 Badge
#define NEO_PIXEL_DATA       5        //Neopixel data connected to port 5 
#define NEO_PIXEL_PWR        48       //Active LOW Neopixel power enable connected to port 48
#define NUMPIXELS            4        //We have 4 neopixels in series
#define NEO_PIXEL_BRIGHTNESS 32       //brightness pin PWM value, max is 128

// TFT Display Ports for OS2024 Badge
#define TFT_CS     10
#define TFT_RST    8  
#define TFT_DC     13
#define TFT_SCLK   12   
#define TFT_MOSI   11  
#define TFT_BL     47

// E-Ink Display ports for OS2024 Badge
#define EPD_DISCHARGE  21
#define EPD_RESET      45
#define EPD_BUSY       38
#define EPD_CS         18
#define EPD_PANEL_ON   40             //Panel unused in OS2024 Badge, route to unused port to prevent silly serial error messages
#define EPD_BORDER     41             //Border unused in OS2024 Badge, route to unused port to prevent silly serial error messages
#define EPD_MISO        9
#define EPD_MOSI       11
#define EPD_CLK        12

//General defines for this example sketch
#define EPD_SIZE        EPD_2_0          //our EPD is the 2 inch 200x96 pixel monochrome display by Pervasive (E2200CS021)
#define LED1            6                //Orange led D1 connected to port 6
#define LARGE_TEXT      7                //large text size for Adafruit_ST7735 screen
#define SMALL_TEXT      2                //small text size for Adafruit_ST7735 screen
#define TFT_ROTATION    3                //Correct rotation for ADAfruit_ST7735 screen on OS2024 badge
#define TFT_BRIGHTNESS  127              //out of 255 max, 50% looks nice
#define COUNTDOWN_TIME  6                //value to countdown before each EPD image cycle (will display as 5 down to 0)
#define TFT_CENTER_X    38               //out of 128 max x position value
#define TFT_CENTER_Y    40               //out of 128 max y position value
#define LOOP_DELAY      75               //main loop runs every 75 milliseconds


// Defin TFT Display
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCLK, TFT_RST);

// Define E-Ink Display
EPD_Class EPD(EPD_SIZE, EPD_PANEL_ON, EPD_BORDER, EPD_DISCHARGE, EPD_RESET, EPD_BUSY, EPD_CS);

// Define Neopixel
Adafruit_NeoPixel pixels(NUMPIXELS, NEO_PIXEL_DATA, NEO_GRB + NEO_KHZ800);

void setup() {
  // put your setup code here, to run once:
  
  // Start Serial monitor
  Serial.begin(9600);
  Serial.println("Begin Program...");
  
  //Setup the Orange LED
  pinMode(LED1, OUTPUT);  // initialize digital pin LED1 as an output

  //Setup the buttons
  pinMode(S4, INPUT_PULLUP);  // initialize digital pin as input with weak pullup enabled
  pinMode(S5, INPUT_PULLUP);  // initialize digital pin as input with weak pullup enabled
  pinMode(S6, INPUT_PULLUP);  // initialize digital pin as input with weak pullup enabled
  pinMode(S7, INPUT_PULLUP);  // initialize digital pin as input with weak pullup enabled

  //Setup Neopixel
  pinMode(NEO_PIXEL_PWR, OUTPUT);                     // initialize neopixel power enable port as output
  digitalWrite(NEO_PIXEL_PWR, LOW);                   // Turn on active low NEOPIXEL power
  pixels.begin();                                     // INITIALIZE NeoPixel strip object (REQUIRED)
  pixels.setBrightness(NEO_PIXEL_BRIGHTNESS);         // set brightness out of 128 max (these things are bright so lets leave low at 32)
  
  //Setup TFT 
  tft.startWrite();                     // begin transactions
  tft.initR(INITR_144GREENTAB);         // initialize a ST7735S chip, green tab 1.44 inch
  tft.fillScreen(ST7735_RED);           // Red background
  tft.setTextColor(ST7735_WHITE);       // White letters
  tft.setRotation(TFT_ROTATION);        // Fix the Orientation
  tft.setTextSize(LARGE_TEXT);          // Use Large Text!!
  tft.endWrite();                       // end transactions
  pinMode(TFT_BL, OUTPUT);              // set the backlight pin as output
  analogWrite(TFT_BL, TFT_BRIGHTNESS);  // apply a duty cycle to backlight pin from 0 to 255

  //Setup EPD pins
  pinMode(EPD_BUSY, INPUT);            // set up EPD Busy pin as inputu
  pinMode(EPD_RESET, OUTPUT);          // set upReset pin as output
  pinMode(EPD_DISCHARGE, OUTPUT);      // set up discharge pin as output
  pinMode(EPD_CS, OUTPUT);             // set up chip select pin as output
  pinMode(EPD_BORDER, OUTPUT);         // set up border pin, unused in OS2024 schematic, assign to unused pin 40 to prevent silly error messages on the serial monitor
  pinMode(EPD_PANEL_ON, OUTPUT);       // set up Panel_on pin, unused in OS2024 schematic, assign to unused pin 41 to prevent silly error messages on the serial monitor
  digitalWrite(EPD_RESET, LOW);        // leave in Not Reset
  digitalWrite(EPD_DISCHARGE, LOW);    // leave in Not Discharge
  digitalWrite(EPD_CS, LOW);           // leave in Not Chip Select
  
  //Make the TFT screen RED
  tft.startWrite();tft.fillScreen(ST7735_RED);tft.endWrite();   //tft start, fillscreen with red, tft end           
  
  Serial.println("Begin Loop...");
}

int lcd_timer = COUNTDOWN_TIME - 1;   //Variable to cycle the TFT screen countdown 
int led_timer = 0;                    //Variable to cycle the orange LED 
int epd_timer = -1;                   //Variable to cycle the EPD image 
int pixel_timer = 0;                  //Variable to cycle neo Pixel LEDs

void loop() {
  // put your main code here, to run repeatedly:

  delay (LOOP_DELAY);                //do this loop every LOOP_DELAY milli seconds, 75 works nice

  //cycle the Orange LED with each tick of led_timer 
  if (led_timer == 1){digitalWrite(LED1, HIGH);led_timer++;} else {digitalWrite(LED1, LOW);led_timer = 0;} led_timer++; 
  //end of code to cycle Orange LED

  //Change out the EPD image every COUNTDOWN_TIME ticks of epd_timer using 3 different images in cat.h, re-initialize the TFT object after EPD image push or else TFT SPI bus will stop working
  if      (epd_timer == ((1 * COUNTDOWN_TIME)-1)){tft.fillScreen(ST7735_RED);EPD.begin();EPD.image_0(jed_bits); EPD.end();tft.initR(INITR_144GREENTAB);tft.setRotation(3);}                      // push image, re-init TFT
  else if (epd_timer == ((2 * COUNTDOWN_TIME)-1)){tft.fillScreen(ST7735_RED);EPD.begin();EPD.image_0(Guitar_bits); EPD.end();tft.initR(INITR_144GREENTAB);tft.setRotation(3);}                   // push image, re-init TFT
  else if (epd_timer == ((3 * COUNTDOWN_TIME)-1)){tft.fillScreen(ST7735_RED);EPD.begin();EPD.image_0(cat_2_0_bits); epd_timer = -1; EPD.end();tft.initR(INITR_144GREENTAB);tft.setRotation(3);}  // push image, reset epd_timer, re-init TFT
  epd_timer++;    // increment epd_timer by 1 each tick
  //end of code to update EPD image

  //Update the TFT countdown screen and show button pushes
  tft.startWrite();                                                                                             //start TFT SPI
  tft.setTextSize(7); tft.setCursor(TFT_CENTER_X, TFT_CENTER_Y); tft.setTextColor(ST7735_RED);                  // set text size, reset cursor position, set text color to red
  if (lcd_timer == (COUNTDOWN_TIME - 1)){tft.print(String(0));} else {tft.print(String(lcd_timer + 1));}        // overwrite the previous loop value in red to make it smoothly dissapear
  tft.setCursor(TFT_CENTER_X, TFT_CENTER_Y); tft.setTextColor(ST7735_WHITE);tft.print(String(lcd_timer));       // reset cursor position, set color to white, print the new value in white to make it appear
  
  //Write any Button Pushes in small text WHITE color to the screen if they are pressed otherwise write it in small text RED color to the screen to make invisible
  if (digitalRead(S4) == 0 ){tft.setTextColor(ST7735_WHITE);tft.setTextSize(2);tft.setCursor(10, 100);tft.print("S4");} else {tft.setTextSize(2);tft.setCursor(10, 100);tft.setTextColor(ST7735_RED);tft.print("S4");}
  if (digitalRead(S5) == 0 ){tft.setTextColor(ST7735_WHITE);tft.setTextSize(2);tft.setCursor(40, 100);tft.print("S5");} else {tft.setTextSize(2);tft.setCursor(40, 100);tft.setTextColor(ST7735_RED);tft.print("S5");}
  if (digitalRead(S6) == 0 ){tft.setTextColor(ST7735_WHITE);tft.setTextSize(2);tft.setCursor(70, 100);tft.print("S6");} else {tft.setTextSize(2);tft.setCursor(70, 100);tft.setTextColor(ST7735_RED);tft.print("S6");}
  if (digitalRead(S7) == 0 ){tft.setTextColor(ST7735_WHITE);tft.setTextSize(2);tft.setCursor(100,100);tft.print("S7");} else {tft.setTextSize(2);tft.setCursor(100, 100);tft.setTextColor(ST7735_RED);tft.print("S7");}
  
  tft.endWrite();                                                                               // end TFT SPI
  if (lcd_timer == 0){lcd_timer = COUNTDOWN_TIME;}                                              // if zero, reset lcd_timer variable for the next countdown
  lcd_timer--;                                                                                  // decrement lcd_timer variable by 1 each tick
  //end of code to Update the TFT countdown and show button pushes

  //illuminate the next Neopixel and set random color
  pixels.clear();                                                                               // turn off pixels
  pixels.setPixelColor(pixel_timer, pixels.Color(random(0,255),random(0,255),random(0,255)));   // set random pixel color RGB value to the next pixel
  pixels.show();                                                                                // turn on pixels
  if (pixel_timer == 3) {pixel_timer=-1;}                                                       // reset pixel timer after cycling through all 4 pixels (0 to 3)
  pixel_timer++;                                                                                // increment pixel_timer each loop tick
  //end of code to illuminate next Neopixel and set random color
}
