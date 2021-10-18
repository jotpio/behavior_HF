import time
import serial
import logging

logging.basicConfig(
    filename="PWR_OFF_projector.log",
    encoding="utf-8",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
)

# setup logger

# configure the serial connections (the parameters differs on the device you are connecting to)
try:
    ser = serial.Serial(
        port="/dev/ttyUSB3",  # change this to corresponding usb port
        baudrate=9600,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        xonoff=False,  # flow control
    )
    ser.isOpen()
    logging.info("Opened port to projector")
except:
    logging.critical("Error on opening port to projector")
    exit

# Reading the data from the serial port. This will be running in an infinite loop.
# https://pyserial.readthedocs.io/en/latest/pyserial_api.html
# https://manuals.plus/m/2eac94e754c5a9eb7705e9fee6b85e975ef8f7bfb50dc04fbc269cdb441e2c9e_optim.pdf

# Power On: <CR>*pow=on#<CR>
# Power Off: <CR>*pow=off#<CR>

# if it's not working test this: https://stackoverflow.com/questions/44317348/pyserial-rs232-9600-8-n-1-send-and-receive-data

# send power on command 10 times
pwr_off_cmd = "<CR>*pow=off#<CR>".encode("ascii")
for i in range(10):
    try:
        ser.write(pwr_off_cmd)
        time.sleep(1)
        logging.debug("Sent POWER OFF command to projector")
    except serial.SerialTimeoutException:
        logging.error("Timeout when sending command to projector via USB.")
    except serial.SerialException:
        logging.error("An unexpected exception occurred while writing to the serial.")
    except:
        logging.error("Error in writing to serial connection to projector")

try:
    ser.close()
except:
    logging.error("Error in closing serial port to projector")

exit
