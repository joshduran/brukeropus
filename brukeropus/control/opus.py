import os, warnings
from brukeropus.control import DDEClient
from brukeropus import OPUSFile

'''Known Direct Commands
ADM=11  switches from rapid-scan to to step-scan mode (error if previous mode was not rapid-scan)
ADM=12  switches from step-scan to rapid-scan mode (error if previous mode was not step-scan)
NPT=x   moves scanning mirror x points from current position (relative movement)
PPT=x   moves scanning mirror x points backward from current position (relative movement)
STP=x   moves scanning mirror to x points from start position (absolute movement)
POS     returns the current position of the scanning mirror
SSE=12  check the accuracy of scanning mirror and max deviation.
VAC=4   evacuates sample compartment
VAC=5   vents sample compartment
FLP=0   opens sample compartment flaps
FLP=1   closes sample compartment flaps
'''


ERROR_CODES = {
    1: 'Not an Opus Command',
    2: 'Unknown Command (similar to #1)',
    3: 'Missing Square Bracket in Command',
    4: 'Function Not Available (Possible missing parameter)',
    5: 'Parameter Name Is Incorrect',
    6: 'Parameter Set Is Incomplete',
    7: 'File Parameter Is Incorrectly Formatted',
    8: 'File(s) Missing Or Corrupt',
    9: 'Opus Could Not Complete The Command',
}


class Opus:
    connected = False

    def connect(self):
        '''Connects class to OPUS software through the DDE interface.  Sets the `connected` attribute to `True` if
        successful.  By default, initializing an `Opus` class will automatically attempt to connect to OPUS.'''
        try:
            self.dde = DDEClient("Opus", "System")
            self.connected = True
        except Exception as e:
            self.connected = False
            warning_text = "Failed to connect to OPUS Software: " + str(e)
            warnings.warn(warning_text, stacklevel=2)
    
    def request(self, req_str, timeout=10000):
        byte_response = self.dde.request(req_str, timeout)
        str_response = byte_response.decode('ascii')#.strip()
        responses = str_response.split('\n')
        responses = [r for r in responses if r != '']
        return responses
    
    def get_version(self):
        return self.request('GET_VERSION')
    
    def get_language(self):
        return self.request('GET_LANGUAGE')
    
    def get_opus_path(self):
        return self.request('GET_OPUSPATH')[1]
    
    def direct_command(self, text_command):
        '''Used to send "direct commands" to the optics bench.

        direct_command('VAC=5') #vents the sample compartment
        direct_command('VAC=4') #evacuates sample compartment
        
        Note: the text_command input should be formatted as a string.'''
        
        return self.request('SendCommand(0, {UNI=' + text_command + '})')
    
    def unload_file(self, filepath):
        '''Unloads a file from the OPUS software from its `filepath`'''
        self.request('UNLOAD_FILE "' + filepath + '"')
    
    def measure_ref(self, timeout=1000000, **kwargs):
        '''Takes a reference measurement using the current settings from advanced experiment.  Also
        takes option **kwargs input which use the OPUS 3-letter parameter keys and values as input
        to customize the measurement.  example:

            measure_ref(nrs=100, res=4) # measures reference with current settings but overriding averages
                to 100 and resolution to 4
                
        The three letter parameters arg names can be any case, i.e. NRS=100 is same as nrs=100'''
        params = self.param_str(**kwargs)
        ok = self.request('MeasureReference(0,' + params + ')', timeout=timeout)
        return ok
    
    def measure_sample(self, unload=False, timeout=1000000, **kwargs):
        '''Takes a reference measurement using the current settings from advanced experiment.  Also
        takes option **kwargs input which use the OPUS 3-letter parameter keys and values as input
        to customize the measurement.  example:

            measure_sample(nss=100, res=4) # measures reference with current settings but overriding averages
                to 100 and resolution to 4

        The three letter parameters arg names can be any case, i.e. NSS=100 is same as nss=100'''
        params = self.param_str(**kwargs)
        output = self.request('MeasureSample(0,' + params + ')', timeout=timeout)
        filepath = output[2][1:-3]
        if unload:
            self.unload_file(filepath)
        return filepath
    
    def check_signal(self, nss=1, **kwargs):
        '''Performs a quick (typically 1 sample) measurement using the current FTIR settings. Current
        settings can be overridden using **kwargs. After measurement is finished, the file is unloaded
        from OPUS so it does not display with other measured data. The function returns an OPUSFile
        object before it deletes the quick measurement file.'''
        filepath = self.measure_sample(unload=True, nss=nss, snm='Python\\Temp', sfm='Check Signal', **kwargs)
        o_file = OPUSFile(filepath)
        os.remove(filepath)
        return o_file
    
    def save_ref(self):
        '''Saves current reference to file (according to current filename and path set in advanced
        experiment) and returns the filename'''
        return self.request('SaveReference()')
    
    def param_str(self, **kwargs):
        '''Takes in an arbitrary number of: key=val kwargs and returns a param string of the following format:

        param_str(nss=100, res=4)
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

    
