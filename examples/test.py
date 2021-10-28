import time
import pyAbacus as pa

pa.constants.DEBUG = False

ports, n = pa.findDevices()
port = list(ports.keys())[0]

pa.open(port)

pa.setSetting(port, 'delay_A', 60)

ans = pa.getAllSettings(port)
print(ans)

stream = pa.Stream(port, ['A'])
stream.start()
time.sleep(20)
stream.stop()

time.sleep(1)

pa.close(port)
