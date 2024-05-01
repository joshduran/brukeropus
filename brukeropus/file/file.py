import datetime, warnings
import numpy as np
from brukeropus.file.utils import get_block_type_label, get_data_key, get_param_label, _print_block_header, _print_cols
from brukeropus.file.parser import (read_opus_file_bytes,
                                    parse_header,
                                    parse_directory,
                                    parse_data_block,
                                    parse_3d_data_block,
                                    parse_param_block,
                                    parse_file_log)


__docformat__ = "google"


def read_opus(filepath):
    '''Return an `OPUSFile` object from an OPUS file filepath.

    The following produces identical results:
        ```python
        data = read_opus(filepath)
        data = OPUSFile(filepath)
        ```
    Args:
        filepath (str or Path): filepath of an OPUS file (typically *.0)

    Returns:
        opus_file (`OPUSFile`): an instance of the `OPUSFile` class containing all data/metadata extracted from the
        file.
    '''
    return OPUSFile(filepath)


class OPUSFile:
    '''Class that contains the data and metadata contained in a bruker OPUS file.

    Args:
        filepath: full path to the OPUS file to be parsed. Can be a string or Path object and is required to initilize
            an `OPUSFile` object.

    Attributes:
        is_opus (`bool`): True if filepath points to an OPUS file, False otherwise. Also returned for dunder 
            `__bool__()`  
        params (`Parameters`): class containing all general parameter metadata for the OPUS file. To save typing, the
            three char parameters from params also become attributes of the `OPUSFile` class (e.g. bms, apt, src)  
        rf_params (`Parameters`): class containing all reference parameter metadata for the OPUS file.  
        data_keys (list): list of all data block keys stored in the file (i.e. sm, rf, t, a, r, igsm, igrf, phsm, etc.).
            These keys become data attributes of the class which return an instance of `Data` or `Data3D`.
        datetime (`datetime`): Returns the most recent datetime of all the data blocks stored in the file (typically
            result spectra)
        directory (`FileDirectory`):  class containing information about all the various data blocks in the file.
        file_log (str): File log containing text about how the file was generated/edited (not always saved)

    Data Attributes:
        **sm:** Single-channel sample spectra  
        **rf:** Single-channel reference spectra  
        **igsm:** Sample interferogram  
        **igrf:** Reference interferogram  
        **phsm:** Sample phase  
        **phrf:** Reference phase  
        **a:** Absorbance  
        **t:** Transmittance  
        **r:** Reflectance  
        **km:** Kubelka-Munk  
        **tr:** Trace (Intensity over Time)  
        **gcig:** gc File (Series of Interferograms)  
        **gcsc:** gc File (Series of Spectra)  
        **ra:** Raman  
        **e:** Emission  
        **dir:** Directory  
        **p:** Power  
        **logr:** log(Reflectance)  
        **atr:** ATR  
        **pas:** Photoacoustic  
    '''

    def __init__(self, filepath: str):
        self.filepath = filepath
        filebytes = read_opus_file_bytes(filepath)
        if filebytes is None:
            self.is_opus = False
        else:
            self.is_opus = True
            self.directory = FileDirectory(filebytes)
            self.params = Parameters(filebytes, self.directory.param_blocks)
            self.rf_params = Parameters(filebytes, self.directory.rf_param_blocks)
            if hasattr(self.directory, 'file_log_block'):
                self.file_log = '\n'.join(parse_file_log(filebytes,
                                                            self.directory.file_log_block.size,
                                                            self.directory.file_log_block.start))
            self.data_keys = []
            for data, status in self.directory.data_and_status_block_pairs:
                key = data.get_data_key()
                if data.is_3d_data():
                    data_class = Data3D(filebytes, data, status)
                else:
                    data_class = Data(filebytes, data, status)
                    if len(data_class.y) < data_class.npt:
                        break  # Don't add data blocks with missing points (rare but observed)
                if 'vel' in self.params.keys():
                    data_class.vel = self.params.vel
                setattr(self, key, data_class)
                self.data_keys.append(key)

    def __str__(self):
        if self.is_opus:
            data_str = ', '.join(self.data_keys)
            return 'OPUS File: spectra: ' + data_str + '   path: ' + str(self.filepath)
        else:
            return 'Not an OPUS file: ' + str(self.filepath)

    def __bool__(self):
        return self.is_opus

    def __getattr__(self, name):
        if name.lower() in self.params.keys():
            return getattr(self.params, name.lower())
        elif name == 'datetime':
            return max(d.datetime for d in self.iter_data() if d.datetime is not None)
        else:
            text = str(name) + ' is not a valid attribute for OPUSFile: ' + str(self.filepath)
            raise AttributeError(text)

    def print_parameters(self, key_width=7, label_width=40, value_width=53):
        '''Prints all the parameter metadata to the console (organized by block)'''
        width = key_width + label_width + value_width
        col_widths = (key_width, label_width, value_width)
        param_blocks = self.directory.param_blocks + self.directory.rf_param_blocks
        for block in param_blocks:
            label = get_block_type_label(block.type)
            _print_block_header(label, width=width)
            _print_cols(('Key', 'Label', 'Value'), col_widths=col_widths)
            for key in block.keys:
                label = get_param_label(key)
                if block.is_rf_param():
                    value = getattr(self.rf_params, key)
                else:
                    value = getattr(self.params, key)
                _print_cols((key.upper(), label, value), col_widths=col_widths)

    def iter_data(self):
        '''Generator that yields the various Data classes from the OPUSFile'''
        for key in self.data_keys:
            yield getattr(self, key)


class FileBlockInfo:
    '''Contains type, size and location information about an OPUS file block.

    This information is parsed from the directory block of an OPUS file and provides the information needed to parse the
    block.

    Args:
        block_type: six integer tuple that describes the type of data in the file block
        size: size of block in number of bytes
        start: pointer to start location of the block within the file.

    Attributes:
        type: six integer tuple that describes the type of data in the file block
        size: size of block in number of bytes
        start: pointer to start location of the block within the file
        keys: tuple of three char keys contained in parameter blocks. This attribute is set by the OPUSFile class only
            when the block is parameter block. This enables grouping parameters by block if desired.
    '''

    __slots__ = ('type', 'size', 'start', 'keys')

    keys: tuple

    def __init__(self, block_type: tuple, size: int, start: int):
        self.type = block_type
        self.size = size
        self.start = start

    def __str__(self):
        label = self.get_label()
        return 'Block Info: ' + label + ' (size: ' + str(self.size) + ' bytes; start: ' + str(self.start) + ')'

    def is_valid(self):
        '''Returns False if FileBlockInfo is undefined (i.e. FileBlockInfo.type == (0, 0, 0, 0, 0, 0))'''
        return self.type != (0, 0, 0, 0, 0, 0)

    def is_data_status(self):
        '''Returns True if FileBlockInfo is a data status parameter block'''
        return self.type[2] == 1

    def is_rf_param(self):
        '''Returns True if FileBlockInfo is a parameter block associated with the reference measurement'''
        return self.type[2] > 1 and self.type[1] == 2

    def is_param(self):
        '''Returns True if FileBlockInfo is a parameter block'''
        return self.type[2] > 1

    def is_directory(self):
        '''Returns True if FileBlockInfo is the directory block'''
        return self.type == (0, 0, 0, 13, 0, 0)

    def is_file_log(self):
        '''Returns True if FileBlockInfo is the file log block'''
        return self.type == (0, 0, 0, 0, 0, 5)

    def is_data(self):
        '''Returns True if FileBlockInfo is a data block or 3D data block'''
        return self.type[2] == 0 and self.type[3] > 0 and self.type[3] != 13

    def is_3d_data(self):
        '''Returns True if FileBlockInfo is a 3D data block (i.e. data series)'''
        return self.is_data() and self.type[5] == 2

    def is_data_status_match(self, data_block_info):
        '''Returns True if FileBlockInfo is a data status block and a match to the data_block_info argument.

        This function is used to match a data status block (contains metadata for data block) with its associated data
        block (contains array data).

        Args:
            data_block_info (FileBlockInfo):  data block being tested as a match.

        Returns:
            is_match (bool): True if FileBlockInfo is data status block and input argument is matching data block'''
        if self.is_data_status():
            return data_block_info.type[:2] == self.type[:2] and data_block_info.type[3:] == self.type[3:]

    def get_label(self):
        '''Returns a friendly string label that describes the block type'''
        return get_block_type_label(self.type)

    def get_data_key(self):
        '''If block is a data block, this function will return an shorthand key to reference that data.

        e.g. t: transmission, a: absorption, sm: sample, rf: reference, smph: sample phase etc. If the block is not
        a data block, it will return None.'''
        if self.is_data():
            return get_data_key(self.type)
        else:
            return None


class Data:
    '''Class containing array data and associated parameter/metadata from an OPUS file.

    Args:
        filebytes: raw bytes from OPUS file. see: `read_opus_file_bytes`
        data_info: `FileBlockInfo` instance of a data block
        data_status_info: `FileBlockInfo` instance of a data status block which contains metadata about the data_info
            block. This block is a parameter block.

    Attributes:
        params: `Parameter` class with metadata associated with the data block such as first x point: `fxp`, last x
            point: `lxp`, number of points: `npt`, date: `dat`, time: `tim` etc.
        y: 1D `numpy` array containing y values of data block
        x: 1D `numpy` array containing x values of data block. Units of x array are given by `dxu` parameter.
        label: human-readable string label describing the data block (e.g. Sample Spectrum, Absorbance, etc.)

    Extended Attributes:
        **wn:** Returns the x array in wavenumber (cm⁻¹) units regardless of what units the x array was originally
            saved in. This is only valid for spectral data blocks such as sample, reference, transmission, etc., not
            interferogram or phase blocks.  
        **wl:** Returns the x array in wavelength (µm) units regardless of what units the x array was originally
            saved in. This is only valid for spectral data blocks such as sample, reference, transmission, etc., not
            interferogram or phase blocks.  
        **f:** Returns the x array in modulation frequency units (Hz) regardless of what units the x array was
            originally saved in. This is only valid for spectral data blocks such as sample, reference, transmission,
            etc., not interferogram or phase blocks.  
        **datetime:** Returns a `datetime` class of when the data was taken (extracted from data status parameter block).  
        **xxx:** the various three char parameter keys from the `params` attribute can be directly called from the 
            `Data` class for convenience. Common parameters include `dxu` (x units), `mxy` (max y value), `mny` (min y
            value), etc.  
    '''
    __slots__ = ('_key', 'params', 'y', 'x', 'label', 'vel')

    def __init__(self, filebytes: bytes, data_info: FileBlockInfo, data_status_info: FileBlockInfo):
        self._key = data_info.get_data_key()
        self.params = Parameters(filebytes, [data_status_info])
        y = parse_data_block(filebytes, size=data_info.size, start=data_info.start, dpf=self.params.dpf)
        self.y = y[:self.params.npt]    # Trim extra values on some spectra
        self.x = np.linspace(self.params.fxv, self.params.lxv, self.params.npt)
        self.label = data_info.get_label()
        self.vel = 0

    def __getattr__(self, name):
        if name.lower() == 'wn' and self.params.dxu in ('WN', 'MI', 'LGW'):
            return self._get_wn()
        elif name.lower() == 'wl' and self.params.dxu in ('WN', 'MI', 'LGW'):
            return self._get_wl()
        elif name.lower() == 'f' and self.params.dxu in ('WN', 'MI', 'LGW'):
            return self._get_freq()
        elif name.lower() in self.params.keys():
            return getattr(self.params, name.lower())
        elif name == 'datetime':
            return self.params.datetime
        else:
            text = str(name) + ' is not a valid attribute for Data: ' + str(self._key)
            raise AttributeError(text)

    def _get_wn(self):
        if self.params.dxu == 'WN':
            return self.x
        elif self.params.dxu == 'MI':
            return 10000. / self.x
        elif self.params.dxu == 'LGW':
            return np.exp(self.x)

    def _get_wl(self):
        if self.params.dxu == 'WN':
            return 10000. / self.x
        elif self.params.dxu == 'MI':
            return self.x
        elif self.params.dxu == 'LGW':
            return 10000 / np.exp(self.x)
    
    def _get_freq(self):
        vel = 1000 * np.float(self.vel) / 7900  # cm/s
        return vel * self.wn


class Data3D(Data):
    '''Class containing 3D array data (series of spectra) and associated parameter/metadata from an OPUS file.

    Args:
        filebytes: raw bytes from OPUS file. see: read_opus_file_bytes
        data_info: FileBlockInfo instance of a 3D data block
        data_status_info: FileBlockInfo instance of a data status block which contains metadata about the data_info
            block. This block is a parameter block.

    Attributes:
        params: Parameter class with metadata associated with the data block such as first x point (fxp), last x point
            (lxp), number of points (npt), date (dat), time (tim) etc.
        y: 2D numpy array containing y values of data block
        x: 1D numpy array containing x values of data block. Units of x array are given by .dxu attribute.
        num_spectra: number of spectra in the series (i.e. length of y)
        label: human-readable string label describing the data block (e.g. Sample Spectrum, Absorbance, etc.)

    Extended Attributes:
        **wn:** Returns the x array in wavenumber (cm⁻¹) units regardless of what units the x array was originally saved
            in. This is only valid for spectral data blocks such as sample, reference, transmission, etc., not
            interferogram or phase blocks.  
        **wl:** Returns the x array in wavelength (µm) units regardless of what units the x array was originally saved
            in. This is only valid for spectral data blocks such as sample, reference, transmission, etc., not
            interferogram or phase blocks.  
        **datetime:** Returns a `datetime` class of when the data was taken (extracted from data status parameter
            block).  
        **xxx:** the various three char parameter keys from the "params" attribute can be directly called from the data
            class for convenience. Several of these parameters return arrays, rather than singular values because they
            are recorded for every spectra in the series, e.g. `npt`, `mny`, `mxy`, `tim`, `nsn`.  
    '''
    __slots__ = ('_key', 'params', 'y', 'x', 'num_spectra', 'label')

    def __init__(self, filebytes: bytes, data_info: FileBlockInfo, data_status_info: FileBlockInfo):
        self._key = data_info.get_data_key()
        self.params = Parameters(filebytes, [data_status_info])
        data = parse_3d_data_block(filebytes, start=data_info.start, dpf=self.params.dpf)
        self.y = data['y'][:, :self.params.npt]    # Trim extra values on some spectra
        self.x = np.linspace(self.params.fxv, self.params.lxv, self.params.npt)
        self.num_spectra = data['num_blocks']
        for key, val in data.items():
            if key not in ['y', 'version', 'offset', 'num_blocks', 'data_size', 'info_size']:
                self.params._params[key] = val
        self.label = data_info.get_label()


class Parameters:
    '''Class containing parameter metadata of an OPUS file.

    Parameters of an OPUS file are stored as key, val pairs, where the key is always three chars.  For example, the
    beamsplitter is stored in the "bms" attribute, source in "src" etc.  A list of known keys, with friendly label can
    be found in `brukeropus.file.constants.PARAM_LABELS`.  The keys in an OPUS file are not case sensitive, and stored
    in all CAPS (i.e. `BMS`, `SRC`, etc.) but this class uses lower case keys to follow python convention.  The class is
    initialized from a list of parameter `FileBlockInfo`.  The key, val items in blocks of the list are combined into
    one parameter class, so care must be taken not to pass blocks that will overwrite each others keys.  Analagous to a
    dict, the keys, values, and (key, val) can be iterated over using the functions: `keys()`, `values()`, and `items()`
    respectively.

    Args:
        filebytes: raw bytes from OPUS file. see: `brukeropus.file.parser.read_opus_file_bytes`
        param_blocks: list of `FileBlockInfo`; every block in the list should be classified as a parameter block.

    Attributes:
        xxx: parameter attributes are stored as three char keys. Which keys are generated depends on the list of
            `FileBlockInfo` that is used to initialize the class. If input list contains a single data status
            `FileBlockInfo`, attributes will include: `fxv`, `lxv`, `npt` (first x-val, last x-val, number of points),
            etc. Other blocks produce attributes such as: `bms`, `src`, `apt` (beamsplitter, source, aperture) etc. A
            full list of keys available in a given Parameters instance are given by the `keys()` method.
        datetime: if blocks contain the keys: `dat` (date) and `tim` (time), the `datetime` attribute of this class will
            be set to a python `datetime` object. Currently, only data status blocks are known to have these keys. If
            `dat` and `tim` are not present in the class, the `datetime` attribute will return `None`.
    '''
    __slots__ = ('_params', 'datetime')

    def __init__(self, filebytes: bytes, param_blocks: list):
        self._params = dict()
        for block_info in param_blocks:
            params = {key.lower(): val for key, val in parse_param_block(filebytes, block_info.size, block_info.start)}
            self._params.update(params)
            block_info.keys = tuple(params.keys())
        self._set_datetime()

    def __getattr__(self, name):
        if name.lower() in self._params.keys():
            return self._params[name.lower()]
        else:
            text = str(name) + ' not a valid attribute. For list of valid parameter keys, use: .keys()'
            raise AttributeError(text)

    def __getitem__(self, item):
        return self._params.__getitem__(item)

    def _set_datetime(self):
        if 'dat' in self.keys() and 'tim' in self.keys():
            date_str = self.dat
            time_str = self.tim
            dt_str = date_str + '-' + time_str[:time_str.index(' (')]
            fmt = '%d/%m/%Y-%H:%M:%S.%f'
            dt = datetime.datetime.strptime(dt_str, fmt)
            self.datetime = dt
        else:
            self.datetime = None

    def keys(self):
        '''Returns a `dict_keys` class of all valid keys in the class (i.e. dict.keys())'''
        return self._params.keys()

    def values(self):
        '''Returns a `dict_values` class of all the values in the class (i.e. dict.values())'''
        return self._params.values()

    def items(self):
        '''Returns a `dict_items` class of all the values in the class (i.e. dict.items())'''
        return self._params.items()


class FileDirectory:
    '''Contains type and pointer information for all blocks of data in an OPUS file.

    `FileDirectory` information is decoded from the raw file bytes of an OPUS file. First the header is read which
    provides the start location of the directory block, number of blocks in file, and maximum number of blocks the file
    supports. Then it decodes the block pointer information from each entry of the file's directory block. Rather than
    store all file blocks in a single list (as it is done in the OPUS file directory), this class sorts the blocks into
    categories: `data`, `data_status`, `params`, `rf_params`, `directory`, and `file_log`.  It also pairs the data
    blocks with their corresponding `data_status` block to simplify grouping y data with the parameters that are used to
    generate x data and other data block specific metadata.

    Args:
        filebytes: raw bytes from OPUS file. see: `brukeropus.file.parser.read_opus_file_bytes`

    Attributes:
        start: pointer to start location of the directory block
        max_blocks: maximum number of blocks supported by file
        num_blocks: total number of blocks in the file
        data_blocks: list of `FileBlockInfo` that contain array data (e.g. sample, reference, phase)
        data_status_blocks: list of `FileBlockInfo` that contain metadata specific to a data block (units, etc.)
        param_blocks: list of `FileBlockInfo` that contain metadata about the measurement sample
        rf_param_blocks: list of `FileBlockInfo` that contain metatdata about the reference measurement
        directory_block: `FileBlockInfo` for directory block that contains all the block info in the file
        file_log_block: `FileBlockInfo` of the file log (changes, etc.)
        data_and_status_block_pairs: (data: `FileBlockInfo`, data_status: `FileBlockInfo`) which pairs the data status
            parameter block (time, x units, y units, etc.) with the data block it informs
    '''

    __slots__ = ('version', 'start', 'max_blocks', 'num_blocks', 'data_blocks', 'data_status_blocks', 'param_blocks',
                 'rf_param_blocks', 'directory_block', 'file_log_block', 'data_and_status_block_pairs')

    def __init__(self, filebytes: bytes):
        self.version, self.start, self.max_blocks, self.num_blocks = parse_header(filebytes)
        self.data_blocks: list = []
        self.data_status_blocks: list = []
        self.param_blocks: list = []
        self.rf_param_blocks: list = []
        self.directory_block: FileBlockInfo
        self.file_log_block: FileBlockInfo
        for block_type, size, start in parse_directory(filebytes, self.start, self.num_blocks):
            block = FileBlockInfo(block_type=block_type, size=size, start=start)
            if block.is_data_status():
                self.data_status_blocks.append(block)
            elif block.is_rf_param():
                self.rf_param_blocks.append(block)
            elif block.is_param():
                self.param_blocks.append(block)
            elif block.is_directory():
                self.directory_block = block
            elif block.is_file_log():
                self.file_log_block = block
            elif block.is_valid():
                self.data_blocks.append(block)
        self.data_and_status_block_pairs = []
        self._pair_data_and_status_blocks()

    def __str__(self):
        data_keys = [b.get_data_key() for b in self.data_blocks]
        data_str = ', '.join(data_keys)
        return 'File Directory: ' + str(self.num_blocks) + ' total blocks; data blocks: (' + data_str + ')'

    def _pair_data_and_status_blocks(self):
        for data_block in self.data_blocks:
            status_matches = [block for block in self.data_status_blocks if block.is_data_status_match(data_block)]
            if len(status_matches) == 0:
                text = 'Warning: No data status block match for data block: ' + str(data_block)
                + '\n\tdata block will be ignored.'
                warnings.warn(text)
            elif len(status_matches) > 1:
                text = 'Warning: Multiple data status block matches for data block: ' + str(data_block)
                + '\n\tMatches:' + '; '.join([str(match) for match in status_matches])
                + '\n\tdata block will be ignored.'
                warnings.warn(text)
            else:
                self.data_and_status_block_pairs.append((data_block, status_matches[0]))
