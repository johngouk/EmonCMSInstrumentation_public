# EmonCMSInstrumentation
I have an Air Source Heat Pump (ASHP), and in the interests of operating it more efficiently, I've instrumented it with a number of tools.

* An ESP32 (packaged in an M5StickC Plus) which interrogates the internal software using a serial procotol - ESPAltherma is the base for that
* A Tuya energy consumption monitor, which is connected to the Tuya cloud and uses a pair of Current Transformers (CT) to mesaure the current in the feeds to the house and HP
* a python script that interrogates the Tuya device to extract data from it and publish it to EmonCMS using MQTT; this last was super-hairy, and involved signing up as a Tuya developer so I could get access to the data directly from the device rather than through the cloud - I hate clouds except when they are mine, or at least, I'm implementing the software on them
* a PZEM-016 energy monitor device, from AliExpress, that uses (another) CT to monitor energy, and exposes its data through RS485 and ModBusRTU, I believe it's called now
* another python script to run on an ESP32 that interrogates the PZEM using a RS485-serial adapter, and sends the data to EmonCMS using HTTP

If you want to use this, I suggest you

* install the appropriate 1.24... minimum version of micropython on your ESP32 - if you have QSPI flash, use that version!
* copy the /lib directory as-is to the root of the ESP32 flash file system (I use Thonny for programming, which makes this easy)
* copy PZEM_EmonHTTPAsync.py to main.py on the ESP32 root
* edit your WiFi and EmonCMS credentials, the EmonCMS URL and the node name you want to use
* connect the PZEM up using an RS485 adapter
* the code uses ESP32 GPIO pins 17(TX) and 16(RX) - you can use any you like that are valid

Then restarting your ESP32 should see the code fire up. If you haven't got a PZEM connected, it will just moan every 10 secs about that.

## Points to Note
1. It uses the micropython logging package extended with my own SwitchFileHandler that checks the on-flash error log daily and if it has exceeded 500k, switches to a new one, saving the old as 'lastLog.log'. Any previous log is deleted! I figured 24 hours or more to realise an error and check the log was probably ok...
2. It uses asyncio, which greatly simplifies doing various tasks at different intervals, and is much easier to code for than Threading, as every routine knows it has control until it hands it back, rather than having to worry about semaphores etc. You can't do Threads on uPython anyway.