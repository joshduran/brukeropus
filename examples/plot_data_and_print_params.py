import numpy as np
from brukeropus import read_opus
from matplotlib import pyplot as plt

# ----------------------------------
# read OPUS file (OPUSFile class), print parameter metadata and plot all data blocks in the file
opus_file = read_opus('file.0')
print('\n\n\n', opus_file)  # spectra and path info
opus_file.print_parameters()  # full parameter info

# Plot each data block in the file in it's own figure
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
