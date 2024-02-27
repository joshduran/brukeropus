from brukeropus import read_opus, find_opus_files
from brukeropus.file import parse_file_and_print
from matplotlib import pyplot as plt
import numpy as np

#----------------------------------
# Script Variables
opus_dir = 'directory\\containing\\opus\\files'  # directory containing OPUS files
opus_dir = r'C:\Users\rubbe\OneDrive\Documents\Data\brukeropus\small set'
max_files = 10  # maximum number of OPUS files to print

#----------------------------------
# Get list of OPUS filepaths from directory and print 
opus_filepaths = find_opus_files(opus_dir, recursive=True)
print('\nFound', len(opus_filepaths), 'OPUS files in:', opus_dir)
print('Printing first', max_files, 'files:')
for i, filepath in enumerate(opus_filepaths):
    if i < max_files:
        print(i, ' ', filepath)

#----------------------------------
# Parse and print all blocks an OPUS file without converting to OPUSFile class (useful for exploring/debugging a file)
print('\n\n\nparse_file_and_print Output:')
parse_file_and_print(opus_filepaths[0])

#----------------------------------
# read OPUS file (OPUSFile class), print parameter metadata and plot all data blocks in the file
opus_file = read_opus(opus_filepaths[0])
print('\n\n\n', opus_file)
opus_file.print_parameters()
for data in opus_file.iter_data():
    if len(data.y.shape) == 1 or data.y.shape[0] == 1:  # Plot 1D array spectra
        plt.figure()
        plt.plot(data.x, data.y.flatten())
        plt.title(data.label)
    if len(data.y.shape) == 2 and data.y.shape[0] > 1:  # Plot 3D array spectra (e.g. time series)
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        x, y = np.meshgrid(data.x, data.nsn)
        z = data.y
        surf = ax.plot_surface(x, y, z, cmap='viridis', linewidth=0, antialiased=False)
        plt.title(data.label)
plt.show()
