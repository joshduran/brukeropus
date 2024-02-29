from brukeropus import find_opus_files
from brukeropus.file import parse_file_and_print

# ----------------------------------
# Script Variables
opus_dir = 'directory\\containing\\opus\\files'  # directory containing OPUS files
max_files = 10  # maximum number of OPUS files to print

# ----------------------------------
# Get list of OPUS filepaths from directory and print
opus_filepaths = find_opus_files(opus_dir, recursive=True)
print('\nFound', len(opus_filepaths), 'OPUS files in:', opus_dir)
print('Printing first', max_files, 'files:')
for i, filepath in enumerate(opus_filepaths):
    if i < max_files:
        print(i, ' ', filepath)

# ----------------------------------
# Parse and print all blocks an OPUS file without converting to OPUSFile class (useful for exploring/debugging a file)
print('\n\n\nparse_file_and_print Output:')
parse_file_and_print(opus_filepaths[0])
