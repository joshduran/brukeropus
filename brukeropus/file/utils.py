import textwrap, re, os
from brukeropus.file.constants import TYPE_CODE_LABELS, PARAM_LABELS, CODE_3_ABR
from brukeropus.file.parser import (read_opus_file_bytes,
                                    parse_header,
                                    parse_directory,
                                    parse_data_block,
                                    parse_3d_data_block,
                                    parse_param_block,
                                    parse_file_log,
)


__all__ = ['find_opus_files', 'get_param_label', 'get_type_code_label', 'get_block_type_label', 'get_data_key',
           'parse_file_and_print']


__docformat__ = "google"


def find_opus_files(directory, recursive: bool = False):
    '''Finds all files in a directory with a strictly numeric extension (OPUS file convention).

    Returns a list of all files in directory that end in .# (e.g. file.0, file.1, file.1001, etc.). Setting recursive
    to true will search directory and all sub directories recursively. No attempt is made to verify the files are
    actually OPUS files (requires opening the file); the function simply looks for files that match the naming pattern.

    Args:
        directory (str or Path): path indicating directory to search
        recursive: Set to True to recursively search sub directories as well

    Returns:
        filepaths (list): list of filepaths that match OPUS naming convention (numeric extension)
    '''
    pattern = re.compile(r'.+\.[0-9]+$')
    file_list = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if pattern.match(filename):
                file_list.append(os.path.join(root, filename))
        if not recursive:
            break
    return file_list


def get_param_label(param: str):
    '''Returns a short but descriptive label for 3-letter parameters. For example, bms returns Beamsplitter.

    The 3-letter parameter input is not case sensitive.  This package includes the majority of parameters that OPUS
    uses, but in the event a parameter label is not known, this function will return: "Unknown XXX" where XXX is the
    unknown 3-letter parameter.

    Args:
        param: three letter parameter code (e.g. bms, src, npt, etc.) [not case sensitive]

    Returns:
        label (str): Human-readable string label for the parameter.
    '''
    try:
        return PARAM_LABELS[param.upper()]
    except KeyError:
        return 'Unknown ' + param.upper()


def get_type_code_label(pos_idx: int, val: int):
    '''Returns the type code label of a file block given the position index and value of the type code.

    The file blocks on an OPUS file feature six-integer type codes, for example (3, 1, 1, 2, 0, 0), that categorize the
    contents of the file block. The positional index defines the category, while the value at that index defines the
    specific type of that category.  For example, the first integer (pos_idx=0), describes the type of data in the
    block, if applicable:

        0: Undefined or N/A,
        1: Real Part of Complex Data,
        2: Imaginary Part of Complex Data,
        3: Amplitude

    This package includes the majority of type codes that OPUS uses, but in the event a type code label is not known,
    this function will return: "Unknown 0 4" where the first number is the position index, and the second is the
    unknown value integer.

    Args:
        pos_idx: positional index of the type code (0 - 5)
        val: value of the type code

    Returns:
        label (str): human-readable string label that describes the type code.
    '''
    try:
        return TYPE_CODE_LABELS[pos_idx][val]
    except KeyError:
        return 'Unknown ' + str(pos_idx) + ' ' + str(val)


def get_block_type_label(block_type: tuple):
    '''Converts a six-integer tuple block type into a human readable label.

    Args:
        block_type: six integer tuple found in the OPUS file directory that describes the block type

    Returns:
        label (str): human-readable string label
    '''
    labels = [get_type_code_label(idx, val) for idx, val in enumerate(block_type) if val > 0
              and get_type_code_label(idx, val) != '']
    return ' '.join(labels)


def get_data_key(block_type: tuple):
    '''Returns a shorthand key for a given data block type: sm, rf, igsm, a, t, r, etc.

    Determines if the data block type is an interferogram, single-channel, absorption, etc. and whether it is associated
    with the sample or reference channel and returns a shortand key-like label: sm, rf, igsm, igrf, a, t, r, etc.  For
    the full data label (e.g. Sample Spectrum, Absorbance) use: get_block_type_label.
    This package includes the majority of type codes that OPUS uses, but in the event a type code label is not known,
    this function will return: "_33" or "sm_33" where 33 will change to the unkown block_type integer value.

    Args:
        block_type: six integer tuple found in the OPUS file directory that describes the block type

    Returns:
        key (str): shorthand string label that can be utilized as a data key (e.g. "sm", "igrf", "a")'''
    if block_type[3] in CODE_3_ABR.keys():
        key = CODE_3_ABR[block_type[3]]
        if block_type[1] == 1:
            key = merge_key(key, 'sm')
        elif block_type[1] == 2:
            key = merge_key(key, 'rf')
        elif block_type[1] > 3:
            key = key + '_' + str(block_type[1])
    else:
        key = '_' + str(block_type[3])
        if block_type[1] == 1:
            key = 'sm' + key
        elif block_type[1] == 2:
            key = 'rf' + key
        elif block_type[1] > 3:
            key = '_' + str(block_type[1]) + key
    return key


def merge_key(key: str, sm: str):
    '''Merges "sm" or "rf" into an abreviated data key.  For special cases like ig or pw, the addition is appended
    (e.g. igsm, phrf), but for other cases, the addition is prepended (e.g. sm_2ch, rf_3ch)'''
    if key[:2] in ['ig', 'ph', 'pw']:
        return key[:2] + sm + key[2:]
    else:
        return sm + key


def parse_file_and_print(filepath, width=120):
    '''Parses an OPUS file and prints the block information as it goes along to the console.

    This function demonstrates the basic usage and interaction of the parsing functions.  It
    can also be used to diagnose a file parsing issue if one comes up.

    Args:
        filepath (str or Path): filepath to an OPUS file.
    '''
    filebytes = read_opus_file_bytes(filepath)
    if filebytes is not None:
        width = 120
        info_col_widths = (28, 15, 16, 61)
        info_col_labels = ('Block Type', 'Size (bytes)', 'Start (bytes)', 'Friendly Name')
        _print_block_header(filepath, width)
        version, dir_start, max_blocks, num_blocks = parse_header(filebytes)
        h_text = '    '.join([
            'Version: ' + str(version),
            'Directory start: ' + str(dir_start),
            'Max Blocks: ' + str(max_blocks),
            'Num Blocks: ' + str(num_blocks)])
        _print_centered(h_text, width)
        _print_block_header('Directory', width)
        blocks = []
        _print_cols(info_col_labels, info_col_widths)
        for info in parse_directory(filebytes, dir_start, num_blocks):
            try:
                vals = [info[0], info[1], info[2], get_block_type_label(info[0])]
                _print_cols(vals, info_col_widths)
                blocks.append(info)
            except Exception as e:
                print('Exception parsing block info: ', e)
        for block_info in blocks:
            try:
                _parse_block_and_print(filebytes, block_info, width=width)
            except Exception as e:
                print('Exception parsing block:', block_info, '\n\tException:', e)
    else:
        print('Selected file is not an OPUS file: ', filepath)


def _print_block_header(label, width):
    'Helper function for: parse_file_and_print'
    print('\n' + '=' * width)
    _print_centered(label, width)


def _print_centered(text, width):
    'Helper function for: parse_file_and_print'
    print(' ' * int((width - len(text)) / 2) + text)


def _parse_block_and_print(filebytes, block_info, width):
    'Helper function for: parse_file_and_print'
    param_col_widths = (10, 45, 45)
    key_width = 10
    key_label_width = 45
    param_col_widths = (key_width, key_label_width, width - key_width - key_label_width)
    param_col_labels = ('Key', 'Friendly Name', 'Value')
    if block_info[0] != (0, 0, 0, 13, 0, 0):
        _print_block_header(get_block_type_label(block_info[0]), width)
        if block_info[0][2] > 0 or block_info[0] == (0, 0, 0, 0, 0, 1):
            _print_cols(param_col_labels, param_col_widths)
            for key, val in parse_param_block(filebytes, block_info[1], block_info[2]):
                _print_cols((key, get_param_label(key), val), param_col_widths)
        elif block_info[0] == (0, 0, 0, 0, 0, 5):
            log = parse_file_log(filebytes, block_info[1], block_info[2])
            for entry in log:
                for line in textwrap.wrap(entry, width=width):
                    print(line)
        elif block_info[0][5] == 2:
            data = parse_3d_data_block(filebytes, block_info[2])
            _print_centered('Num Blocks: ' + str(data['num_blocks']), width)
            _print_centered('Store Table: ' + str(data['store_table']), width)
            print(data['y'])
        elif block_info[0][0] > 0 and block_info[0][1] > 0 and block_info[0][2] == 0 and block_info[0][3] > 0:
            array = parse_data_block(filebytes, block_info[1], block_info[2])
            print(array)
        else:
            _print_centered('Undefined Block Type: Raw Bytes', width)
            print(filebytes[block_info[2]: block_info[2] + block_info[1]])


def _print_cols(vals, col_widths,):
    'Helper function for: parse_file_and_print'
    string = ''
    for i, val in enumerate(vals):
        col_width = col_widths[i]
        val = str(val)
        if len(val) <= col_width - 2:
            string = string + val + ' ' * (col_width - len(val))
        else:
            string = string + val[:col_width - 5] + '...  '
    print(string)
