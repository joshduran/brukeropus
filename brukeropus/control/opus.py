import os
from brukeropus.control import DDEClient
from brukeropus import read_opus

__docformat__ = "google"

ERROR_CODES = {
    1: 'Not an Opus Command',
    2: 'Unknown Opus Command',
    3: 'Missing Square Bracket in Command',
    4: 'Function Not Available (Possible missing parameter)',
    5: 'Parameter Name Is Incorrect',
    6: 'Parameter Set Is Incomplete',
    7: 'File Parameter Is Incorrectly Formatted',
    8: 'File(s) Missing Or Corrupt',
    9: 'Opus Could Not Complete The Command',
}


class Opus:
    '''Class for communicating with currently running OPUS software using DDE interface.  Class automatically attempts
    to connect to OPUS software upon initialization.'''
    dde = None
    connected = False
    error_string = 'Error'

    def connect(self):
        '''Connects class to OPUS software through the DDE interface.  Sets the `connected` attribute to `True` if
        successful.  By default, initializing an `Opus` class will automatically attempt to connect to OPUS.'''
        try:
            self.dde = DDEClient("Opus", "System")
            self.connected = True
        except Exception as e:
            self.connected = False
            raise Exception("Failed to connect to OPUS Software: " + str(e))

    def disconnect(self):
        '''Disconnects DDE client/server connection.'''
        if self.connected:
            self.dde.__del__()
            self.dde = None
            self.connected = False

    def raw_query(self, req_str: str, timeout=10000):
        '''Sends command/request string (`req_str`) to OPUS and returns the response in byte format.

        Args:
            req_str: The request string to send to OPUS over DDE
            timeout: timeout in milliseconds.  If a response is not recieved within the timeout period, an exception is
                raised.

        Returns:
            response: response from OPUS software through DDE request in bytes format.'''
        return self.dde.request(req_str, timeout)

    def parse_response(self, byte_response: bytes, decode='ascii'):
        '''Parses the byte response from a raw DDE request query.  If an error is detected in the request, an Exception
        is raised.  If successful, a boolean, string or list of strings will be returned as appropriate.

        Args:
            byte_response: response from OPUS software through DDE request in bytes format.
            decode: format used to decode bytes into string (e.g. 'ascii' or 'utf-8')

        Returns:
            response: parsed response from OPUS software (bool, string, or list of strings depending on request)'''
        str_response = byte_response.decode(decode)
        responses = str_response.split('\n')
        responses = [r for r in responses if r != '']
        if len(responses) == 0:
            raise Exception('Error with DDE request: "' + req_str + '"; no response recieved...')
        elif responses[0].startswith(self.error_string):
            error = self._parse_error(responses[0])
            raise Exception('Error with DDE request: "' + req_str + '"; ' + error)
        else:
            responses = [r for r in responses if r != 'OK']
            if len(responses) == 0:
                return True
            elif len(responses) == 1:
                return responses[0]
            else:
                return responses

    def _parse_error(self, response: str):
        try:
            code = int(response[response.rfind('ID: ') + 4:])
            if code in ERROR_CODES.keys():
                return ERROR_CODES[code]
            else:
                return response
        except:
            return response

    def query(self, req_str: str, timeout=10000, decode='ascii'):
        '''Sends a command/request and returns the parsed response.

        Args:
            req_str: The request string to send to OPUS over DDE
            timeout: timeout in milliseconds.  If a response is not recieved within the timeout period, an exception is
                raised.
            decode: format used to decode bytes into string (e.g. 'ascii' or 'utf-8')

        Returns:
            response: parsed response from OPUS software (bool, string, or list of strings depending on request)
        '''
        response = self.raw_query(req_str=req_str, timeout=timeout)
        return self.parse_response(response, decode=decode)

    def close_opus(self):
        '''Closes the OPUS application. Returns `True` if successful.'''
        return self.query('CLOSE_OPUS')

    def get_param_label(self, param: str):
        '''Get the label for a three character parameter code (e.g. BMS, APT, DTC, etc...).

        Args:
            param: three character parameter code (case insensitive)

        Returns:
            label: short descriptive label that defines the parameter'''
        return self.query('PARAM_STRING ' + param.upper())

    def get_param_options(self, param: str):
        '''Get the parameter setting options for a three character parameter code. Only valid for
        enum type parameters (e.g. BMS, APT, DTC, etc...).

        Args:
            param: three character parameter code (case insensitive)

        Returns:
            options: list of valid options (strings) for the given parameter'''
        result = self.query('ENUM_STRINGS ' + param.upper())
        if type(result) is list:
            return result[1:]
        else:
            return False

    def get_version(self):
        '''Get the OPUS software version information'''
        return self.query('GET_VERSION_EXTENDED')

    def get_opus_path(self):
        '''Get the absolute path to the OPUS software directory (where PARAMTEXT.bin and other instrument specific files
        are located)'''
        return self.query('GET_OPUSPATH')

    def send_command(self, text_command: str, timeout=10000):
        '''Used to send "Direct Commands" to the optics bench. Useful for manually moving motors, etc. from accessories
        and other low-level operations such as controlling the scanning mirror movement.

        Examples:
            send_command('VAC=5') # vents the sample compartment
            send_command('VAC=4') # evacuates sample compartment

        Args:
            text_command: string command as you would enter into "Direct Command" input of OPUS
            timeout: timeout in milliseconds to wait for response

        Returns:
            response: parsed response from OPUS software (typically boolean confirmation)'''

        return self.query('SendCommand(0, {UNI=' + text_command + '})')

    def evacuate_sample(self):
        '''Evacuates the sample compartment'''
        return self.send_command('VAC=4')

    def vent_sample(self):
        '''Vents the sample compartment'''
        return self.send_command('VAC=5')

    def close_flaps(self):
        '''Closes vacumm flaps between optics bench and sample compartment'''
        return self.send_command('FLP=1')

    def open_flaps(self):
        '''Opens vacumm flaps between optics bench and sample compartment'''
        return self.send_command('FLP=0')

    def unload_file(self, filepath: str):
        '''Unloads a file from the OPUS software from its `filepath`

        Args:
            filepath: full path of the file to be unloaded in the software.

        Returns:
            response: `True` if successful.'''
        return self.query('UNLOAD_FILE "' + filepath + '"')

    def unload_all(self):
        '''Unloads all files from OPUS software'''
        return self.query('UnloadAll()')

    def measure_ref(self, timeout=1000000, **kwargs):
        '''Takes a reference measurement using the current settings from advanced experiment.  Also
        takes option **kwargs input which use the OPUS 3-letter parameter keys and values as input
        to customize the measurement.  example:

            measure_ref(nrs=100, res=4) # measures reference with current settings but overriding averages to 100 and
                resolution to 4

        Args:
            timeout: timeout in milliseconds to wait for response
            kwargs: any valid three character parameter code (case insensitive)

        Returns:
            response: `True` if successful
            '''
        params = self._param_str(**kwargs)
        ok = self.query('MeasureReference(0,' + params + ')', timeout=timeout)
        return ok

    def measure_sample(self, unload=False, timeout=1000000, **kwargs):
        '''Takes a reference measurement using the current settings from advanced experiment.  Also
        takes option **kwargs input which use the OPUS 3-letter parameter keys and values as input
        to customize the measurement.  example:

            measure_sample(nss=100, res=4) # measures sample with current settings but overriding averages to 100 and
                resolution to 4

        Args:
            unload: whether to unload the file from OPUS after measurement is complete (to allow moving/renaming, etc.)
            timeout: timeout in milliseconds to wait for response
            kwargs: any valid three character parameter code (case insensitive)

        Returns:
            filepath: absolute filepath to measured sample file'''
        params = self._param_str(**kwargs)
        output = self.query('MeasureSample(0,' + params + ')', timeout=timeout)
        filepath = output[1][1:-3]
        if unload:
            self.unload_file(filepath)
        return filepath

    def check_signal(self, nss=1, **kwargs):
        '''Performs a quick (typically 1 sample) measurement using the current FTIR settings. Current settings can be
        overridden using **kwargs. After measurement is finished, the file is unloaded from OPUS and deleted. The
        function returns an `OPUSFile` object before it deletes the quick measurement file.

        Args:
            nss: number of sample scans to average (default is 1, i.e. no averaging)
            kwargs: any valid three character parameter code (case insensitive)

        Returns:
            opus_file: `OPUSFile` object generated by quick measurement'''
        filepath = self.measure_sample(unload=True, nss=nss, **kwargs)
        opus_file = read_opus(filepath)
        os.remove(filepath)
        return opus_file

    def save_ref(self):
        '''Saves current reference to file (according to current filename and path set in advanced experiment) and
        returns the filename.

        Returns:
            filepath: absolute path to saved reference file'''
        output = self.query('SaveReference()')
        filepath = output[1][1:-3]
        return filepath

    def _param_str(self, **kwargs):
        '''Takes in an arbitrary number of: key=val kwargs and returns a param string of the following format:

        _param_str(nss=100, res=4)
        returns: {NSS=100,RES=4}

        These param strings are used by the measure_ref and measure_sample functions to specify
        experimental parameters.'''
        params = []
        for arg, val in kwargs.items():
            params.append(arg.upper() + '=' + str(val))
        if len(params) > 0:
            return '{' + ','.join(params) + '}'
        else:
            return ''

    def __bool__(self):
        return self.connected

    def __init__(self):
        self.connect()
        if self.connected:
            self.opus_path = self.get_opus_path()
