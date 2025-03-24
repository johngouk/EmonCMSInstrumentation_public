# EmonCMSInstrumentation
I have an Air Source Heat Pump (ASHP), and in the interests of operating it more efficiently, I've instrumented it with a number of tools. Energy consumption, monitored on a real-time basis, is critical to analysing system performance. I had previously used a Tuya energy consumption monitor, which is connected to the Tuya cloud and uses a pair of Current Transformers (CT) to measure the current in the feeds to the house and HP. However, it was occasionally unreliable, for whatever reason, required a Python script to poll it anyway, and was always at risk of Tuya closing the developer account I had to open to make it work!

Then I found the PZEM-016 energy monitor device, from AliExpress, that uses (another) CT to monitor energy, and exposes its data through RS485 and ModBusRTU, I believe it's called now. The OEM forum had a very useful thread about it, which suggested it might be within 1% of a high quality, accurate energy monitor. So I developed a python script to run on an ESP32 that interrogates the PZEM using a RS485-serial adapter, and sends the data to EmonCMS using HTTP, over WiFi.

If you want to use this, and you haven't done this before, I suggest you

1. Get an RS485-serial interface - lots on eBay/Amazon, uses the MAX3485 chip
2. Get a PZEM-016 with opening CT - I got mine from AliExpress, cheap, quick
3. ESP32 dev board - any will do probably, a sufficiently small one could even go in the PZEM case; I haven't tried ESP8266, might require C++ for more compact code
4. Get a copy of Thonny, the Python editor for programming, which makes this easy; you'll need to select ESP32 and connect it with USB
5. Install the ppropriate 1.24... minimum version of micropython on your ESP32 - if you have QSPI flash, use that version (requires separate download and esptool.py)!
6. Copy the entire GitHub repository to your computer
7. Edit/save main.py to provide your WiFi and EmonCMS credentials, the EmonCMS URL and the node name you want to use for your data in EmonCMS
8. Copy the /lib directory as-is to the root of the ESP32 flash file system (Thonny makes this bit easy)
9. Copy main.py on to on the ESP32 root
10. Connect the PZEM up to the ESP32 using the RS485 adapter
11. The code uses ESP32 GPIO pins 17(TX) and 16(RX) - you can use any you like that are valid
12. Put the CT around the feed wire (the live one) to the HP
13. Wire the PZEM to the mains supply - I used a 3-core mains flex and fused mains plug - the PZEM needs power and also to monitor the AC voltage and frequency
14. The PZEM-016 provides 5V which I use to power the ESP, so the whole thing is self-powered

Then restarting your ESP32 should see the code fire up. If you haven't got a PZEM connected, it will just moan every 10 secs about that.

## Points to Note
1. Uses the micropython logging package extended with my own SwitchFileHandler that checks the on-flash error log daily and if it has exceeded 500k, switches to a new one, saving the old as 'lastLog.log'. Any previous log is deleted! I figured 24 hours or more to realise an error and check the log was probably ok...
2. Uses asyncio, which greatly simplifies doing various tasks at different intervals, and is much easier to code for than Threading, as every routine knows it has control until it hands it back, rather than having to worry about semaphores etc. You can't do Threads on uPython anyway.