# Bruker OPUS
`brukeropus` is a Python package for interacting with Bruker's OPUS spectroscopy software. Currently, the package can
read OPUS data files and communicate/control OPUS through the DDE interface (e.g. for scripting measurement sequences).
## Reading OPUS Data Files
`brukeropus` can read the binary data files saved by OPUS. The parsing algorithm in this package is more complete than
previous efforts, with a goal to achieve 100% extraction accuracy.
### Features
- Extracts spectral data (e.g. sample, reference, absorbance, transmittance, etc.)
- Extracts 3D spectral data (e.g. spectral time series)
- Extracts file metadata (e.g. beamsplitter, source, aperture, etc.) with human readable metadata labels for over 2000
parameters (extracted directly from OPUS software parameter file)
- Very fast data parsing and assigning to `OPUSFile` class (limited by disk I/O)
- Low-level parsing functions are well documented and could be used to build your own custom OPUS file class if
`OPUSFile` does not suit your needs)
### Usage
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
### Known Limitations
- I have only tested this on ~5000 files generated in my lab (all very similiar) as well as a handful of files I've
found online (most of which had some error when being read by other tools). This package is capable of reading all of
those files, but thorough testing on a wide variety of files is incomplete.

    - If you have a file that cannot be read by `brukeropus`, please open an issue with a description about the file and
    what seems to be failing.  Also provide a link for me to download the file.  Make sure the file can be read by OPUS
    first (i.e. if the file is corrupted and unreadable by OPUS then `brukeropus` will not be able to read it either).
## Controlling OPUS Software
`brukeropus` can send commands and perform queries to an OPUS software instance through the DDE communication protocol.
OPUS must be open and logged in on the same PC where `brukeropus` is called from to operate.
### Features
- Initiate a sample or reference measurement
- Change/define measurement parameters prior to performing measurement (useful for sweeping parameters like aperture
size, mirror velocity, etc.)
- Send commands for interacting with motors and other accessories (e.g. moving mirrors, rotating polarizers, etc.)
- Control vacuum operation for vacuum-equipped spectrometers (e.g. Vertex 80V FTIR)
- Unload files from OPUS software (so they can be unlocked for moving, renaming, etc.)
### Usage
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
## Future Plans
- Continue to improve the file reader towards 100% compliance (currently no known discrepancies)
- Add additional control interface options (e.g. http or .dll)
## Installation
**Requirements**
- Python 3.6+
- numpy

**Optional**
- matplotlib (for plotting examples)
### pip
```python
pip install brukeropus
```
https://pypi.org/project/brukeropus/
## Documentation
https://joshduran.github.io/brukeropus/brukeropus.html

