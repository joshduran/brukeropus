'''
`brukeropus` is a Python package for interacting with Bruker's OPUS spectroscopy software. Currently, the package can
read OPUS data files and communicate/control OPUS software using the DDE communication protocol)

### Installation
`brukeropus` requires `python 3.6+` and `numpy`, but `matplotlib` is needed to run the plotting examples.  You can
install with pip:
```python
pip install brukeropus
```

### Namespace
`brukeropus` provides direct imports to the following:
```python
from brukeropus import find_opus_files, read_opus, OPUSFile, Opus
```
All other file functions or classes can be directly imported from the `brukeropus.file` or `brukeropus.control`
submodules, e.g.:
```python
from brukeropus.file import parse_file_and_print
```
It is recommended that you do **not** import from the fully qualified namespace, e.g.:
```python
from brukeropus.file.utils import parse_file_and_print
```
as that namespace is subject to change. Instead import directly from `brukeropus` or its first level submodules.

### Reading OPUS Files (Basic Usage)
```python
from brukeropus import read_opus
from matplotlib import pyplot as plt

opus_file = read_opus('file.0')  # Returns an OPUSFile class

opus_file.print_parameters()  # Pretty prints all metadata in the file to the console

if 'a' in opus_file.data_keys:  # If absorbance spectra was extracted from file
    plt.plot(opus_file.a.x, opus_file.a.y)  # Plot absorbance spectra
    plt.title(opus_file.sfm + ' - ' + opus_file.snm)  # Sets plot title to Sample Form - Sample Name
    plt.show()  # Display plot
```
More detailed documentation on the file submodule can be found in `brukeropus.file`

### Controlling OPUS Software (Basic Usage)
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
More detailed documentation on the control submodule can be found in `brukeropus.control`.
'''

from brukeropus.file import OPUSFile, read_opus, find_opus_files
from brukeropus.control import Opus
