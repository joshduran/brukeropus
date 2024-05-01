'''
The `brukeropus.control` submodule of `brukeropus` includes the `Opus` class for communicating with OPUS software. The
`Opus` class currently supports communication through the Dynamic Data Exchange (DDE) protocol.  This class can be used
to script measurement sweeps and perform various low-level operations (e.g. move mirrors, rotate polarizers, etc.). In
order to communicate with OPUS, the software must be open, logged in, and running on the same PC as `brukeropus`.
### Initializing/verifying connection to OPUS Software
```python
from brukeropus import Opus

opus = Opus()  # initialization of class automatically connects to open OPUS software
print(opus.get_version())  # prints the current OPUS software version
```
### Get information about a parameter (e.g. DTC, APT, VEL).
```python
opus = Opus()
param = 'vel'
print(opus.get_param_label(param))
print(opus.get_param_options(param))
```
### Perform a measurement sweep
```python
from brukeropus import opus, read_opus
from matplotlib import pyplot as plt

opus = Opus()  # Connects to actively running OPUS software

apt_options = opus.get_param_options('apt') # Get all valid aperture settings

for apt in apt_options[2:-2]: # Loop over all but the two smallest and two largest aperature settings
    filepath = opus.measure_sample(apt=apt, nss=10, unload=True) # Perform measurement and unload file from OPUS
    data = read_opus(filepath) # Read OPUS file from measurement
    plt.plot(data.sm.x, data.sm.y, label=apt) # Plot single-channel sample spectra
plt.legend()
plt.show()
```
For complete `Opus` documentation, see: `brukeropus.control.opus`
'''
from brukeropus.control.dde import DDEClient
from brukeropus.control.opus import *
