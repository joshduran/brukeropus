# Bruker OPUS
`brukeropus` is a Python package for interacting with Bruker's OPUS spectroscopy software. Currently, the package can
read OPUS data files.
## Reading OPUS Data Files
`brukeropus` can read the binary data files saved by OPUS. The parsing algorithm in this package is more complete than
previous efforts, with a goal to achieve 100% extraction accuracy.
### Features
- Extracts spectral data (e.g. sample, reference, absorbance, transmittance, etc.)
- Extracts 3D spectral data (e.g. spectral time series)
- Extracts file metadata (e.g. beamsplitter, source, aperture, etc.)
- Very fast data parsing and assigning to `OPUSFile` class (limited by disk I/O)
- Parsing functions are documented to provide a living framework/documentation of the OPUS file format (they could also
be used to build your own custom OPUS file class if `OPUSFile` does not suit your needs)
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
- While all metadata can be be extracted as key: val pairs, the keys are stored as three characters (e.g. BMS, SRT, SRC)
and are not particularly descriptive.  This package has human readable labels for over 100 of these metadata keys, but
it is not complete.

    - OPUS software should be using a local file (perhaps PARAMS.bin) to convert these keys to human readable lables.
    it would be ideal to extract these labels directly from this file rather than manually adding them by hand as is
    currently done.

- I have only tested this on ~5000 files generated in my lab (all very similiar) as well as a handful of files I've
found online (most of which had some error when being read by other tools). The package is capable of reading all of
those files, but thorough testing on a wide variety of files is incomplete.

    - If you have a file that cannot be read by brukeropus, please open an issue with a description about the file and
    what seems to be failing.  Also provide a link for me to download the file.  Make sure the file can be read by OPUS
    first (i.e. if the file is corrupted and unreadable by OPUS then brukeropus will not be able to read it either).
## Future Plans
- Continue to improve the file reader
- Add an API for controlling OPUS software (for scripting measurements using python)
- Add a basic GUI for browsing OPUS files
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

