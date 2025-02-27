import os, sys
# Relative Imports
TEST_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(TEST_DIR)
sys.path.insert(0, PARENT_DIR)
from brukeropus import read_opus, find_opus_files, OPUSFile
from brukeropus.file.utils import _print_centered


def get_all_blocks(opusfile: OPUSFile) -> list:
    '''Returns a list of all `FileBlock` in an `OPUSFile` instance.'''
    blocks = [opusfile.directory.block] + opusfile.special_blocks + opusfile.unknown_blocks + \
        opusfile.unmatched_data_blocks + opusfile.unmatched_data_status_blocks
    if hasattr(opusfile, 'params'):
        blocks = blocks + opusfile.params.blocks
    if hasattr(opusfile, 'rf_params'):
        blocks = blocks + opusfile.rf_params.blocks
    for d in opusfile.iter_all_data():
        blocks = blocks + d.blocks
    return blocks


def filter_data_with_mismatched_num_blocks(data: list) -> list:
    '''Filters a list of `OPUSFile` to include only instances where `num_blocks` from the header does not match the
    length of the parsed blocks in the directory and the length of all sorted blocks in the `OPUSFile`'''
    data = [d for d in data if d]
    mismatched = []
    for o in data:
        blocks = get_all_blocks(o)
        if not (len(blocks) == len(o.directory.block.data) and len(blocks) == o.directory.num_blocks):
            mismatched.append(o)
    return mismatched


def filter_data_with_unknown_blocks(data: list) -> list:
    '''Filters a list of `OPUSFile` to include only instances where there are unknown/uncategorized blocks.  This
    function ignores blocks of type: (0, 0, 0, 0, 0, 0) because OPUS also appears to ignore those blocks.'''
    data = [d for d in data if d]
    unknown = [d for d in data if len(d.unknown_blocks) > 0]
    return [d for d in unknown if any(b.type != (0, 0, 0, 0, 0, 0) for b in d.unknown_blocks)]


def filter_data_that_failed_to_parse(data: list) -> list:
    '''Filters a list of `OPUSFile` to include only instances where there are blocks whose `bytes` attribute were not
    set to zero or whose `parser` attribute has not been set (indicates parsing was not attempted or there was an
    exception during parsing).'''
    data = [d for d in data if d]
    bad_parse = []
    for o in data:
        blocks = get_all_blocks(o)
        blocks = [b for b in blocks if b.type != (0, 0, 0, 0, 0, 0)]
        if any(b.parser is None or b.bytes != b'' for b in blocks):
            bad_parse.append(o)
    return bad_parse


def find_all_files(directory: str) -> list:
    '''Recursively finds all files (regardless of filetype) in a directory.'''
    filepaths = []
    for root, dirs, filenames in os.walk(directory):
        filepaths = filepaths + [os.path.join(root, f) for f in filenames]
    return filepaths


def print_pass(message):
    'Prints a formatted pass test message'
    print('| Passed |  ' + message)


def print_fail(message):
    'Prints a formatted failed test message'
    print('| FAILED |  ' + message)


if __name__ == "__main__":
    # ==============================================================================================
    # Test Report Settings
    directory = os.path.join(TEST_DIR, 'files')  # Directory with test files
    width = 120  # Width of report in characters
    print_non_opus_ext = False  # Whether to print all files without OPUS numeric extension
    # ----------------------------------------------------------------------------------------------
    # Initialize Data
    opus_files = find_opus_files(directory, recursive=True)
    opus_data = [read_opus(f) for f in opus_files]
    for o in opus_data:
        o.rel_path = '\\' + os.path.relpath(o.filepath, directory)  # Add rel_path attribute for printing
    # ----------------------------------------------------------------------------------------------
    # Print header
    print()
    print('=' * width)
    _print_centered('Test File Directory: ' + str(directory), width=width)
    # ----------------------------------------------------------------------------------------------
    # Find all files and check for presence of non-opus files (based on extension and reading bytes)
    all_files = find_all_files(directory)
    non_opus_ext = [f for f in all_files if f not in opus_files]
    opus_ext_but_not_opus = [d for d in opus_data if not d]
    print(len(all_files), 'files found')
    print(len(opus_files), 'files with OPUS numeric extension.')
    if len(non_opus_ext) > 0 and print_non_opus_ext:
        print('Files without numeric extension:')
        for f in non_opus_ext:
            print('   ', '\\' + os.path.relpath(f, directory))
    if len(opus_ext_but_not_opus) > 0:
        print('Files with numeric extension that are not valid OPUS files:')
        for o in opus_ext_but_not_opus:
            print('   ', o.rel_path)
    # ----------------------------------------------------------------------------------------------
    # Check that parsed directory block and sorted blocks in OPUSFile match in length and agree with
    #   num_blocks value from header
    mismatched = filter_data_with_mismatched_num_blocks(opus_data)
    print('.' * width)
    if len(mismatched) == 0:
        print_pass('All file blocks were found and consistent (' + str(len(opus_data)) + ' files)')
    else:
        print_fail('Some mismatched block numbers: ' + str(len(mismatched)) + '/' + str(len(opus_data)) + ' files')
        for o in mismatched:
            print('\n', o.rel_path,
                  '\n    num_blocks:', o.directory.num_blocks,
                  '\n    directory block length:', len(o.directory.block.data),
                  '\n    length of blocks found in OPUSFile:', len(get_all_blocks(o)))
    # ----------------------------------------------------------------------------------------------
    # Check that `OPUSFile.directory.blocks` are clear (should be sorted elsewhere, otherwise redundant)
    redundant = [d for d in opus_data if d and len(d.directory.blocks) > 0]
    print('.' * width)
    if len(redundant) == 0:
        print_pass('OPUSFile.directory.blocks are all clear (No redundant data blocks in class)')
    else:
        print_fail('Redundant data blocks found in OPUSFile.directory.blocks (Memory ineffiency):')
        for o in redundant:
            print('   ', o.rel_path)
    # ----------------------------------------------------------------------------------------------
    # Checks for any OPUS files with unknown/uncategorized data blocks
    unknown = filter_data_with_unknown_blocks(opus_data)
    print('.' * width)
    if len(unknown) == 0:
        print_pass('No files with unknown/uncategorized blocks [Ignoring (0, 0, 0, 0, 0, 0) blocks]')
    else:
        print_fail('Files with unknown blocks: ' + str(len(unknown)) + '/' + str(len(opus_data)) + ' files')
        for o in unknown:
            print('   ', o.rel_path + ':', [b.type for b in o.unknown_blocks])
    # ----------------------------------------------------------------------------------------------
    # Checks for any `OPUSFile` that contains any unparsed block(s)
    bad_parse = filter_data_that_failed_to_parse(opus_data)
    print('.' * width)
    if len(bad_parse) == 0:
        print_pass('Every block was successfully parsed')
    else:
        print_fail('Some blocks were not parsed successfully:')
        for o in bad_parse:
            print('   ', o.rel_path)
    # ----------------------------------------------------------------------------------------------
    # Checks that PARAM_LABELS was correctly loaded from param_labels.json
    print('.' * width)
    if len(PARAM_LABELS.keys()) > 2000:
        print_pass('param_labels.json successfully parsed: ' + str(len(PARAM_LABELS.keys())) + ' parameters')
    else:
        print_fail('Expected more parameter labels to be parsed, only found: ' + str(len(PARAM_LABELS.keys())))
    # # ==============================================================================================
    # # File Statistics
    # print('_' * width)
    # _print_centered('Test File Statistics', width=width)
    # data_keys = set()
    # for o in opus_data:
    #     for key in o.all_data_keys:
    #         data_keys.add(key)
    # print('Data Keys (' + str(len(data_keys)) + '):', '  '.join(sorted(list(data_keys))))