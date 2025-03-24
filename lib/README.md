# Useful libraries
In order to simplify setting up the ESP32 each time I zap it, I've saved the relevant libraries in this handy lib folder. I just copy this onto a fresh ESP32 before doing anything.

## time.mpy
This is the pre-compiled version of the time micropython-lib extension that provides strftime. Imma slob.

## logging.mpy
Likewise, this is the logging code, which has to be on the ESP32 (obvs!)

## ESPLogRecord
This is my extension to the logging Record class which handles the time processing better, and enables both (msec) and (asctime) keywords for log entries. If the ESP32 is newly started, and isn't connected to WiFi, the date/time will be from beginning of Epoch i.e. 0, but the msecs are fine! If you do an ntptime.settime() after connecting, it all magically works out. Strangely, the micropython REPL nobbles the ESP32 RTC to be correct if you run code from that rather than downloading it to run as main.py. Hmm. 

## umodbus
This is the very good code that speaks modbus to the PZEM, I can thoroughly recommend it.
