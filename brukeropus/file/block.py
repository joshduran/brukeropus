from brukeropus.file.labels import get_data_key
from brukeropus.file.constants import TYPE_CODE_LABELS
from brukeropus.file.parse import (parse_directory,
                                   parse_params,
                                   parse_data,
                                   parse_data_series,
                                   parse_text,
                                   parse_report)


__docformat__ = "google"


class BlockType(tuple):
    '''Six-integer tuple representing the category (type) of block within an OPUS file.

    Each block in an OPUS file is categorized with six integers, for example (3, 1, 1, 2, 0, 0). This class stores the
    integers as a tuple, but extends the class to provide a few useful functions.

    Args:
        block_type: six integers found in the OPUS file directory that describe the block type.

    Attributes:
        label: human-readable label that describes the block category
    '''

    def get_label(self):
        '''Converts a six-integer tuple block type into a human readable label.

        This package includes the majority of type codes that OPUS uses, but in the event a type code label is not known,
        this function will return: "Unknown 0 4" where the first number is the position index, and the second is the
        unknown value integer.

        Args:
            block_type: six integer tuple found in the OPUS file directory that describes the block type

        Returns:
            label (str): human-readable string label
        '''
        labels = [self._get_sub_type_label(idx) for idx in range(len(self)) if self[idx] > 0
                  and self._get_sub_type_label(idx) != '']
        return ' '.join(labels)

    def _get_sub_type_label(self, pos_idx: int):
        '''Returns the sub-type label of a file block given the position index and value of the type code.

        Args:
            pos_idx: positional index of the type code (0 - 5)

        Returns:
            label (str): human-readable string label that describes the type code at that index.
        '''
        try:
            return TYPE_CODE_LABELS[pos_idx][self[pos_idx]]
        except KeyError:
            return 'Unknown ' + str(pos_idx) + ' ' + str(self[pos_idx])

    def get_aligned_tuple_str(self, pad=1):
        return f'{self[0]}' + f'{self[1]:2}' + f'{self[2]:3}' + f'{self[3]:3}' + f'{self[4]:2}' + f'{self[5]:2}'

    def __repr__(self):
        return 'BlockType((' + ', '.join([str(i) for i in self]) + '))'

    def __str__(self):
        return self.get_aligned_tuple_str() + '   ' + self.get_label()

    def __new__(cls, iterable):
        instance = super().__new__(cls, iterable)
        if len(instance) != 6 or any(type(i) != int for i in instance):
            raise ValueError('BlockType input must be a 6-integer iterable, but a value of:' + str(iterable) + ' was given')
        return instance

    def __init__(self, iterable):
        super().__init__()
        self.label = self.get_label()


class FileBlock:
    '''Generic OPUS file block.

    This class initializes with the most basic file block info from the file directory: type, size, and start location
    as well as the raw bytes from the file (which can subsequently be parsed).

    Args:
        filebytes: raw bytes of the file
        block_type: six integer tuple that describes the type of data in the file block
        size: size of block in number of bytes
        start: pointer to start location of the block within the file

    Attributes:
        type: six integer tuple that describes the type of data in the file block
        size: size of block in number of bytes
        start: pointer to start location of the block within the file
        bytes: raw bytes of file block (set to zero bytes if successfully parsed)
        data: parsed data if successful. Could be: `list`, `str`, `np.ndarray` or `dict` depending on the block type.
        parser: name of parsing function if parsing was successful
    '''

    __slots__ = ('type', 'size', 'start', 'bytes', 'data', 'parser', 'parse_error', 'keys')

    def __init__(self, filebytes: bytes, block_type: tuple, size: int, start: int):
        self.bytes = filebytes[start: start + size]
        self.type = BlockType(block_type)
        self.size = size
        self.start = start
        self.data = None
        self.parser = None
        self.parse_error = None

    def __str__(self):
        label = self.get_label()
        return 'FileBlock: ' + label + ' (size: ' + str(self.size) + ' bytes; start: ' + str(self.start) + ')'

    def _try_parser(self, parser):
        try:
            self.data = parser(self.bytes)
            if type(self.data) is dict:
                self.keys = list(self.data.keys())
            self._clear_parsed_bytes(parser=parser)
        except Exception as e:
            self.parse_error = 'Error parsing (' + parser.__name__ + '): ' + str(e)

    def _clear_parsed_bytes(self, parser):
        '''Clear raw bytes that have been parsed (and log the parser for reference)'''
        self.parser = parser.__name__
        self.bytes = b''

    def is_data_status(self):
        '''Returns True if `FileBlock` is a data status parameter block'''
        return self.type[2] == 1

    def is_rf_param(self):
        '''Returns True if `FileBlock` is a parameter block associated with the reference measurement (not including
        data status blocks)'''
        return self.type[2] > 1 and self.type[1] == 2

    def is_param(self):
        '''Returns True if `FileBlock` is any parameter block (could be data status, rf param, sample param, etc.)'''
        return self.type[2] > 0 or self.type == (0, 0, 0, 0, 0, 1)

    def is_sm_param(self):
        '''Returns True if `FileBlock` is a parameter block associated with sample/result measurement (not including
        data status blocks)'''
        return self.is_param() and not self.is_data_status() and not self.is_rf_param()

    def is_directory(self):
        '''Returns True if `FileBlock` is the directory block'''
        return self.type == (0, 0, 0, 13, 0, 0)

    def is_file_log(self):
        '''Returns True if `FileBlock` is the file log (aka 'history') block'''
        return self.type == (0, 0, 0, 0, 0, 5)

    def is_report(self):
        '''Returns True if `FileBlock` is a test report'''
        return self.type in [(0, 0, 0, 0, 0, 3), (0, 0, 0, 0, 0, 4)] or (self.type[2] == 0 and self.type[3] not in [0, 13] and self.type[5] == 5)

    def is_data(self):
        '''Returns True if `FileBlock` is a 1D data block (not a data series)'''
        return self.type[2] == 0 and self.type[3] not in [0, 13] and self.type[5] not in [2, 5]

    def is_data_series(self):
        '''Returns True if `FileBlock` is a data series block (i.e. 3D data)'''
        return self.type[2] == 0 and self.type[5] == 2

    def get_label(self):
        '''Returns a friendly string label that describes the block type'''
        return self.type.label

    def get_data_key(self):
        '''If block is a data block, this function will return a shorthand key to reference that data.

        e.g. t: transmission, a: absorption, sm: sample, rf: reference, phsm: sample phase etc. If the block is not
        a data block, it will return `None`.'''
        if self.is_data() or self.is_data_series():
            return get_data_key(self.type)
        else:
            return None

    def get_parser(self):
        '''Returns the appopriate file block parser based on the type code (None if not recognized)'''
        if self.is_directory():
            return parse_directory
        elif self.is_file_log():
            return parse_text
        elif self.is_param():
            return parse_params
        elif self.is_report():
            return parse_report
        elif self.is_data_series():
            return parse_data_series
        elif self.is_data():
            return parse_data
        else:
            return None

    def parse(self):
        '''Determines the appropriate parser for the block and parses the raw bytes.  Parsed data is stored in `data`
        attribute and `bytes` attribute is set empty to save memory'''
        parser = self.get_parser()
        if parser is not None:
            self._try_parser(parser)
