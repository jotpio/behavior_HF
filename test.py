import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import time


formatter = logging.Formatter("%(asctime)s %(levelname) -8s %(message)s")

logger = logging.getLogger("user_input_logger")
handler = TimedRotatingFileHandler(
    "/home/hf-robofish/Desktop/user_input", when="S", interval=5
)
handler.setFormatter(formatter)
# handler.setLevel(logging.CRITICAL)
logger.addHandler(handler)

for _ in range(10):
    logger.warning(datetime.now())
    time.sleep(1)

print("test1234434234234")

# logger2 = logging.getLogger("debug_logger")

# handler2 = TimedRotatingFileHandler(
#     "/home/user1/RoboTracker_HF/logs/behavior_prints/out", when="S", interval=5
# )
# logger2.addHandler(handler2)
# logger2.setLevel(logging.DEBUG)

# for _ in range(10):
#     logger2.info(_)
#     time.sleep(1)
