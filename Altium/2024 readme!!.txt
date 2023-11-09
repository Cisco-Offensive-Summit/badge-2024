The 2024 badge Schematic and Layout started from the 2023 badge; it uses the same technology (4 layer PCB5 mil minimum trace and space)

The changelist, taken from the badge group meeting requests 8-23-2023:

Change Processor to ESP32-S3-WROOM-1-N16R8, 1965-ESP32-S3-WROOM-1-N16R8CT-ND 
Add a 2nd E-inc SPI screen - (Recommend E2200CS021-ND instead of 1528-1028-ND for better availablility and less cost; avoids ada-fruit parts)
Add a E-inc screen connector - (609-1200-2-ND)
Remove all Cap sense Buttons
Add (4) RGB LED Thruhole (COM-12986, COM-12999, COM12877 by sparkfun which uses same WS2812 protocol as magtag)
Add (4) Thru Hole Hard Buttons (use PTS636 SL43 LFS buttons), and make all buttons thruhole (include S1, S2)
Include QWIIC, Stemma QT connector, and Stemma connector (Qwiic, Stemma QT - SM04B-SRSS-TB, Stemma - 455-S4B-PH-SM4-TBTR-ND)
Change to ESP32-S3 for direct USB comms,
Change all Testpoints to match the IO port they are connected to (IO4-->TP4, IO41 -->TP41, etc.)
Keep the  Micro LIPO module, do not Add LIPO Battery charger circuit - (MCP73831T-2ACI)
Keep the Micro LIPO module, do not Change Battery footprint to LIPO connector - (455-1719-ND)
Keep the Micro LIPO module, do not change P5 to direct USB header 2073-USB4105-GF-ATR-ND






