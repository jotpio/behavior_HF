from  datetime import datetime, timedelta
import time
from collections import deque

a=deque([], 10)
print(a)
b=0
while(True):
    a.append(b)
    b += 1

    print(list(a))

    time.sleep(1)