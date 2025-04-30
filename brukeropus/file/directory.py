from brukeropus.file.block import FileBlock
from brukeropus.file.parse import (parse_header,
                                   parse_directory,
                                   )


__docformat__ = "google"


class FileDirectory:
    '''Contains type and pointer information for all blocks of data in an OPUS file.

    `FileDirectory` information is decoded from the raw file bytes of an OPUS file. First the header is read which
    provides the start location of the directory block, number of blocks in file, and maximum number of blocks the file
    supports. Then it decodes the block pointer information from each entry of the file's directory block to create a
    `FileBlock` instance, initiates the block parsing, and adds the parsed block to the `blocks` attribute.

    Args:
        filebytes: raw bytes from OPUS file. see: `brukeropus.file.parser.read_opus_file_bytes`

    Attributes:
        start: pointer to start location of the directory block
        max_blocks: maximum number of blocks supported by file
        num_blocks: total number of blocks in the file
        blocks: list of `FileBlock` from the file. The class parses these blocks upon initilization of the class.
    '''
    def __init__(self, filebytes: bytes):
        self.version, self.start, self.max_blocks, self.num_blocks = parse_header(filebytes)
        size = self.max_blocks * 3 * 4
        self.blocks = []
        self.parse_error_blocks = []
        self.toc = []
        for block_type, size, start in parse_directory(filebytes[self.start: self.start + size]):
            block = FileBlock(filebytes=filebytes, block_type=block_type, size=size, start=start)
            block.parse()
            if block.parse_error:
                self.parse_error_blocks.append(block)
            else:
                self.blocks.append(block)


def is_data_status_type_match(data_block: FileBlock, data_status_block: FileBlock) -> bool:
    '''Checks if data and data status blocks are a match based soley on the block type.

    This check correctly and accurately matches blocks most of the time, but is occasionally not sufficient on its own
    (e.g. when multiple spectra of the same exact type are stored in a single file)'''
    t1 = data_status_block.type
    t2 = data_block.type
    return t1[:2] == t2[:2] and t1[3:] == t2[3:]


def is_data_status_val_match(data_block: FileBlock, data_status_block: FileBlock) -> bool:
    '''Checks if min(data) and max(data) match up with the data status parameters: MNY and MXY.

    When multiple spectra of the same type exist in a file, this is used to distinguish if the data and data status
    blocks are a good match.  This can reduce the number of duplicate matches, but is not generally sufficient to
    fully eliminate duplicate matches.

    See test file: `Test Vit C_Glass.0000_comp.0`'''
    if data_block.is_data():
        try:
            ds = data_status_block.data
            if len(data_block.data) < ds['npt']:
                return False
            else:
                y = ds['csf'] * data_block.data[:ds['npt']]
                return y.min() == ds['mny'] and y.max() == ds['mxy']
        except:
            return True # If error, can't rule out the match
    else:
        return True # Don't rule out data series at this time (no example files to test)


def is_valid_match(data_block: FileBlock, data_status_block: FileBlock) -> bool:
    '''Checks that number of points in data status are less than or equal to length of parsed data block.

    This does not apply to data series. While rare, it is occasionally necessary to remove these bad matches.

    See test file: `unreadable.0000`'''
    if data_block.is_data() and len(data_block.data) < data_status_block.data['npt']:
        return False
    else:
        return True


def pair_data_and_status_blocks(blocks: list) -> list:
    '''Takes a list of `FileBlock` and returns a list of matching (data, data status) blocks for further processing.

    All valid data blocks have an associated data status parameter block that contains y-scaling and x-axis info.
    Generally, these blocks can be easily paired with one another by using the block type. However, some files can
    contain multiple data blocks with the same exact type, which leads to duplicate matches and requires further
    inspection to accurately pair.  This function uses the following logical sequence to accurately pair these blocks:

        1. Pair by type and isolate singular matches from duplicate matches
        2. For duplicate matches, check min(data) and max(data) match data status MNY and MXY (including CSF scaling)
        3. Again isolate singular matches from duplicate matches
        4. For remaining duplicate matches, remove any matches that are already in the singular match list.
        5. Again isolate singular matches (ideally no remaining duplicate matches at this point)
        6. Remove invalid matches from the singular match list if len(data) is < data status NPT (invalid condition)
        7. Sort the matches in reverse order of where the data blocks are stored in the file (presume last is most
           recently added, and therefore final spectra which was true for limited test files).

    For the very limited test files available, this is sufficient to accurately pair all the blocks, but it seems
    plausible that it will not be sufficient for all files that have duplicate data type entries. More test files
    required for thorough testing.
    '''
    data_status = [b for b in blocks if b.is_data_status() and type(b.data) is not str]
    data = [b for b in blocks if b.is_data() or b.is_data_series() and type(b.data) is not str]
    type_matches = []
    for d in data:
        type_matches.append((d, [b for b in data_status if is_data_status_type_match(d, b)]))
    single_matches = [(m[0], m[1][0]) for m in type_matches if len(m[1]) == 1]
    multi_matches = [match for match in type_matches if len(match[1]) > 1]
    val_matches = []
    for d, matches in multi_matches:
        val_matches.append((d, [b for b in matches if is_data_status_val_match(d, b)]))
    single_matches = single_matches + [(m[0], m[1][0]) for m in val_matches if len(m[1]) == 1]
    multi_matches = [match for match in val_matches if len(match[1]) > 1]
    reduced_matches = []
    single_starts = [m[1].start for m in single_matches]
    for d, matches in multi_matches:
        reduced_matches.append((d, [b for b in matches if b.start not in single_starts]))
    single_matches = single_matches + [(m[0], m[1][0]) for m in reduced_matches if len(m[1]) == 1]
    multi_matches = [match for match in reduced_matches if len(match[1]) > 1]

    single_matches = [match for match in single_matches if is_valid_match(match[0], match[1])] # remove invalid

    single_matches.sort(key=lambda pairs: pairs[0].start, reverse=True) # last spec seems to be OPUS preference
    return single_matches