import hashlib
import sys

print('supervision-log-first-marker', flush=True)
for index in range(18000):
    print(str(index) + ' ' + hashlib.shake_256(str(index).encode()).hexdigest(1024))
print('supervision-log-last-marker', flush=True)
