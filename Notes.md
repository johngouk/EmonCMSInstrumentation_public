# Notes on EmonCMS Python

* requests - have to do my own URL encoding!
* need to do ntptime before ESPLogRecord works, but fixed a problem
* MQTT - imported; need to remove extra code examples!
>>> import mip
>>> mip.install("github:peterhinch/micropython-mqtt")
saved it in the EmonCMS directory
* Added check of time to execute loop contents and removed it from sleep_ns;
required adding import math and math.ceil()

* log file is 27971 bytes for 337 records in about an hour, or 28k per hour
how big could it get? 24hr = 671304 bytes! Huge. Horrible.
* Using my ESP32-S3 N16R8, I get gc.mem_free = 8314576,  flash_size = 8388608
so should be ok for 24 hours?

* Could use ping to check if network available to host?