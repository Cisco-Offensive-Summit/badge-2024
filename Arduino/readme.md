### OS_BADGE_2024_Example - 
#### An Arduino C code example sketch created in Arduino IDE 2.3.2 that demonstrates the 2024 badge peripherals:  
Blink the Orange LED  
Print to TFT screen  
PWM TFT backlight control  
Print to EPD screen 
Illuminate Neopixel LEDs  
Test Hard Buttons (report to TFT screen)

*** Note that this sketch is intended to show how to can program the 2024 Offensive Summit Badge in an Arduino environment.  The original 2024 badge firmware that was installed when you received the badge is written in Circuit Python and details for programming the 2024 Offensive Summit Badge using Circuit Python can be found [here](https://github.com/Cisco-Offensive-Summit/badge-2024/tree/main/firmware).  

#### You will need the files in the /libraries directory; copy these to your local /Arduino/libraries directory before compiling.  

Setup of Arduino Environment:

Tools --> Board --> esp32 --> ESP32S3 DEV Module  
Port: "/dev/cu.usbmodemXXXXX"  
USB CDC On Boot: Enabled  
CPU Frequency "240MHz (WiFi)"   
Core Debug Level:  "Warn"  
USB DFU On Boot: "Disabled"  
Erase All Flash Before Sketch Upload: "Enabled"  
Events Run On: "Core 1"  
Flash Mode: "QIO 80MHz"  
Flash Size: "16MB (128Mb)"  
JTAG Adapter: "Disabled"  
Arduino Runs On: "Core 1"  
USB Firmware MSC On Boot: "Disabled"  
Partition Scheme: "Minimal(1.3MB APP/700KB SPIFFS)"  
PSRAM: "Disabled"  
Upload Mode: "UART0/Hardware CDC"  
Upload Speed "115200"  
USB Mode "Hardware CDC and JTAG"  
Zigbee Mode: "Disabled"  
Programmer "Esptool"  




