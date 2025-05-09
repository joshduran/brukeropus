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
        parse_error_blocks: list of `FileBlock` that encountered an error when attempting to parse the binary data.
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


