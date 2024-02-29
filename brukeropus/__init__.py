'''
`brukeropus` is a Python package for interacting with Bruker's OPUS spectroscopy software. Currently, the package can
read OPUS data files, but the intention is for future releases to introduce new functionality (e.g. controlling OPUS
for scripting measurements)

### Installation
`brukeropus` requires `python 3.6+` and `numpy`, but `matplotlib` is needed to run the plotting examples.  You can
install with pip:
```python
pip install brukeropus
```

### Namespace
`brukeropus` provides direct imports to the following:
```python
from brukeropus import find_opus_files, read_opus, OPUSFile
```
All other file functions can be directly imported from the `brukeropus.file` submodule, e.g.:
```python
from brukeropus.file import parse_file_and_print
```
It is recommended that you do **not** import from the fully qualified namespace, e.g.:
```python
from brukeropus.file.utils import parse_file_and_print
```
as that namespace is subject to change. Instead import directly from `brukeropus` or its submodule `brukeropus.file`.

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
'''

from brukeropus.file import OPUSFile, read_opus, find_opus_files
from brukeropus.control import Opus
