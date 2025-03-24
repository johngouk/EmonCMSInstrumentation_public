'''
    PZEM_Emon.py
    Script that polls a Modbus connected energy monitor (PZEM-016) and sends the
    data to EmonCMS using HTTP

    The data item names can be modified to whatever you want, I just used names that
    were already in my system to prevent data loss.
    
    NOTE: This uses the custom ESPLogRecord, which requires time.time() to return the
    actual Unix Epoch time i.e. lots of seconds! This requires use of the ntptime.settime()
    call BEFORE any calls to logging!! Hence the print() statements in the network
    connection code
'''
import machine
import esp
import network
import ntptime
import requests
import json
import time
import mip
import os
import gc
import math
import asyncio
import logging
from ESPLogRecord import ESPLogRecord
import SwitchFileHandler

# These url processing functions are required because micropython requests module
# doesn't do the encoding, unlike the CPython version, to save space (?!)
def url_escape(s): # Translate payload to URL-encoded
    return ''.join(c if c.isalpha() or c.isdigit() else '%%%02x' % ord(c) for c in s)

def url_querystring_encode(params):
  return "&".join("{}={}".format(url_escape(n), url_escape(v)) for n, v in params.items())


print('Flash space:' , esp.flash_size()-esp.flash_user_start())

logSwitchPeriod =  24*3600 # Seconds!
logMaxSize = 500000
logFileName = '/error.log'
lastLogFileName = '/lastLog.log'
'''
    Edit credentials, URL, EmonCMS node name!!
'''
ssid = "ssid"   # WiFi SSID
pwd = "wifipwd" # WiFi password
url = 'http://emonpi.local/input/post' # Local EmonCMS URL - probably won't be different!
node = 'yourNode'   # Whatever you want your data grouped under on the Inputs page
apikey = '0123456789Abcdef0123456789ABCDEF'     # Your APIkey for write

# the following definition is for an ESP32
rtu_pins = (17, 16)         # (TX, RX)
PzemPollInterval = 10000; # 10 secs


# Create log
# This provides output on the console and also to a file on the ESP32 Flash
# The main log entity logging level controls the overall logging level - use INFO or DEBUG to see more
log = logging.getLogger('PZEM')
log.setLevel(logging.ERROR)
log.record = ESPLogRecord()

# Create console handler and set level to debug
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Create file handler and set level to error
file_handler = SwitchFileHandler.SwitchFileHandler(logFileName, mode="a")
file_handler.setLevel(logging.ERROR)

# Create a formatter
formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s")

# Add formatter to the handlers
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to log
log.addHandler(stream_handler)
log.addHandler(file_handler)


def set_time():
    try:
        ntptime.settime()
        #(year, month, mday, hour, minute, second, weekday, yearday)
        log.info('Time set: %s', time.gmtime())
    except Exception as e:
        print('Error in ntptime %s',e)

def do_connect(ssid='ssid', key='pwd'):
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network... {}'.format(ssid))
        wlan.connect(ssid, key)
        while not wlan.isconnected():
            pass
    winfo = wlan.ifconfig()
    print('network config: IP:{} Mask:{} Gway: {} DNS:{}'.format(winfo[0],winfo[1], winfo[2],winfo[3]))
    set_time()

lastSwitchTime = 0

async def flush_log_task():
    global lastSwitchTime
    while True:
        file_handler.flush()
        if lastSwitchTime == 0:
            lastSwitchTime = time.time() # Don't do anything the first time
        else:
            now = time.time()
            logFileSize = os.stat(logFileName)[6]
            if (now - lastSwitchTime > logSwitchPeriod) and (logFileSize > logMaxSize): # It's been 24 hours
                log.info('Switching log')
                lastSwitchTime = now
                file_handler.switchLog(logFileName, lastLogFileName)

        await asyncio.sleep(1)

async def set_time_task():
    while True:
        set_time()
        await asyncio.sleep(36000) # update every 10 hours
    

async def main():
    print('ESP32 startup ...')
    do_connect(ssid, pwd)
    
    asyncio.create_task(flush_log_task())
    asyncio.create_task(set_time_task())
    
    # If you have copied the lib directory onto the ESP32, this will always be loaded...
    log.info ('Connected ok... installing Modbus')
    modbusLoaded = False
    try:
        os.listdir('/lib/umodbus')
        log.info('modbus already loaded')
        modbusLoaded = True
    except Exception as e:
        log.info('modbus not present... loading')
        # Otherwise this is a handy example of using mip!
        try:
            mip.install('github:brainelectronics/micropython-modbus')
        except Exception as e:
            log.error('Failed modbus install: %s', e)
            exit()
    from umodbus.serial import Serial as ModbusRTUMaster

    # RTU Host/Master setup

    uart_id = 1
    slave = ModbusRTUMaster(
        pins=rtu_pins,          # given as tuple (TX, RX)
        # baudrate=9600,        # optional, default 9600
        # data_bits=8,          # optional, default 8
        # stop_bits=1,          # optional, default 1
        # parity=None,          # optional, default None
        # ctrl_pin=12,          # optional, control DE/RE
        uart_id=uart_id         # optional, default 1, see port specific documentation
    )
    log.info (f"UART:{uart_id} TX:{rtu_pins[0]} RX:{rtu_pins[1]}")

    params = {}
    params['node'] = node
    params['apikey'] = apikey
    log.debug('MemFree: %d', gc.mem_free())
    count = 0
    while True:
        t1 = time.time_ns()
        log.info (f"Trying... {count}")
        gc.collect()
        log.debug('MemFree: %d', gc.mem_free())
        modbusError = False
        try:
            reg_status = slave.read_input_registers(slave_addr=1, starting_addr=0, register_qty=9)
        except Exception as e:
            log.error('Modbus error: %s',e)
            modbusError = True
        if not modbusError:
            log.info (f'Status of Input regs: {reg_status}')
            energyData = {}
            # The data item names can be changed to whatever you require
            energyData['voltage'] =(reg_status[0] * 0.1)                              # Voltage(0.1V)
            energyData['current'] =((reg_status[1] + (reg_status[2] << 16)) * 0.001)  # Current(0.001A)
            energyData['power'] =((reg_status[3] + (reg_status[4] << 16)) * 0.1)      # Power(0.1W)
            energyData['energy_forward'] =((reg_status[5] + (reg_status[6] << 16)) * 0.001)# Energy(1Wh)
            energyData['frequency'] =(reg_status[7] * 0.1)                              # Frequency
            energyData['power_factor'] =(reg_status[8] * 0.01)                        # Power Factor
            energyJson = json.dumps(energyData)
            params['fulljson'] = energyJson # This overwrites the value every loop
            #print(params)
            #print (url_querystring_encode(params))
            try:
                fullUrl = url + '?' + url_querystring_encode(params)
                response = requests.get(fullUrl)
                if response.status_code != 200:
                    log.error('Response code: %d text: %s', response.status_code, response.text)
            except Exception as e:
                log.error('Exception during request: %s', e)
            finally:
                pass
            if count >= 60: # Just making an occasional noise to demonstrate working
                log.debug('Working... last result %d: %s', response.status_code, response.text)
                count = 0;
        count = count + 1
        # Following attempts to stay close to N second data interval 
        # ns is 1000000000, ms is 1000
        diff = math.ceil((time.time_ns()-t1)/1000000) # Make ns into ms
        #print("diff:", diff)
        await asyncio.sleep_ms(max(PzemPollInterval-diff, 1)) # Don't want a negative...

if __name__ == '__main__':
    try:
        # start the main async tasks
        asyncio.run(main())
    finally:
        # reset and start a new event loop for the task scheduler
        asyncio.new_event_loop()
