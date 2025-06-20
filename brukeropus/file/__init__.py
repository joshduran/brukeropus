'''
The `brukeropus.file` submodule of `brukeropus` includes all the functions and classes for reading and exploring OPUS
files. This includes both high-level functions like `read_opus` that returns an `OPUSFile` class, as well as low-level
parsing functions like `parse_directory` that returns data extracted directly from the binary OPUS file bytes.  This
overview documentation will focus on the high-level functions which will be useful for most users.  If you are
interested in using the low-level parsing functions, perhaps to make your own data class or customize how files are
read, refer to: `brukeropus.file.parse` which contains all the low-level parsing functions.
## Finding OPUS Files
OPUS files are typically saved with a numeric file extension (e.g. file.0, file.1, file.1001).  This makes searching for
a list of OPUS files in a directory a little more cumbersome than a traditional "*.csv" search.  To address this,
`brukeropus` includes a `find_opus_files` function:
```python
from brukeropus import find_opus_files

filepaths = find_opus_files(r'path\\to\\opus\\files', recursive=True)
```
Which will assign a list of filepaths that match the numeric extension formatting of OPUS files. For full documentation,
see `brukeropus.file.utils.find_opus_files`.
## Reading OPUS Files
`brukeropus` parses OPUS files and assembles them into an `OPUSFile` object that contains the extracted data (and
metadata) within the file.  You can generate an `OPUSFile` object in one of two ways:
```python
from brukeropus import read_opus, OPUSFile

filepath = r'path\\to\\opusfile.0'

data = read_opus(filepath)
same_data = OPUSFile(filepath)
```
In the above code, `data` and `same_data` are both `OPUSFile` objects with identical data.
## Using the `OPUSFile` Class
OPUS files all start with the same first four *magic bytes*.  If the file does not start with these bytes (i.e. is not
a valid OPUS file), the `OPUSFile` class will logically evaluate to `false`:
```python
data = read_opus('file.pdf')
if data:
    print(data)
else:
    print(data.filepath, 'is not an OPUS file')
```
The `OPUSFile` class provides an interface for accessing the data (stored as blocks) in an OPUS file.  Accessible data
includes:

**Parameters** (`brukeropus.file.params`): measurement metadata

**Data** (`brukeropus.file.data.Data`): measurements spectra (1D)

**DataSeries** (`brukeropus.file.data.DataSeries`): series of measurements spectra (3D)

**Report** (`brukeropus.file.report`): tabular report info (e.g. multi-evaluation test reports)

To view a quick summary of the data contained in an `OPUSFile` instance, simply print it to the console:

```python
data = read_opus('file.0')
print(data)
```
```console
========================================================================================================================
                                                 OPUS File: file.0
Attribute      Class type          Description
――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
params         Parameters          Optical, Fourier Transform, Acquisition, Sample Origin, Instrument Status Parameters
rf_params      Parameters          Instrument Status, Optical, Acquisition, Fourier Transform Reference Parameters
rf             Data                Reference Spectrum
igrf           Data                Reference Interferogram
a              Data                Absorbance
sm             Data                Sample Spectrum
phsm           Data                Sample Phase
igsm           Data                Sample Interferogram
history        str                 History log of file
――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――
```
The output listed here will depend on what data blocks were saved in the OPUS file.  The following sections will go
over the various data class types in more detail.

###Parameters (brukeropus.file.params.Parameters)

The metadata in an OPUS file is stored in  `Parameters` classes.  These classes can be stored in the `params` and
`rf_params` attributes which contain the sample and reference parameter metadata respectively.

To view all parameter metadata in the file, you can print to the console using the class method: `print_parameters`.
This will let you view all the key, value parameter data extracted from the file with labels for what the parameter keys
are referring to wherever known.

```python
data = read_opus('file.0')
data.print_parameters()
```
<details>
<summary>Example `print_parameters` Output</summary>
<p>
```console
====================================================================================================
                                 Sample/Result Parameters (params)

....................................................................................................
                                         Optical Parameters
Key    Label                                   Value
ACC    Accessory                               TRANS *010A984F
APR    ATR Pressure                            0
APT    Aperture Setting                        1 mm
BMS    Beamsplitter                            KBr-Broadband
CHN    Measurement Channel                     Sample Compartment
DTC    Detector                                RT-DLaTGS [Internal Pos.1]
HPF    High Pass Filter                        0
LPF    Low Pass Filter                         10.0
LPV    Variable Low Pass Filter (cm-1)         4000
OPF    Optical Filter Setting                  Open
PGN    Preamplifier Gain                       3
RDX    Extended Ready Check                    0
SRC    Source                                  MIR
VEL    Scanner Velocity                        10.0
ADC    External Analog Signals                 0
SON    External Sync                           Off

....................................................................................................
                                    Fourier Transform Parameters
Key    Label                                   Value
APF    Apodization Function                    B3
HFQ    End Frequency Limit for File            500.0
LFQ    Start Frequency Limit for File          10000.0
NLI    Nonlinearity Correction                 0
PHR    Phase Resolution                        100.0
PHZ    Phase Correction Mode                   ML
SPZ    Stored Phase Mode                       NO
ZFF    Zero Filling Factor                     2

....................................................................................................
                                       Acquisition Parameters
Key    Label                                   Value
ADT    Additional Data Treatment               0
AQM    Acquisition Mode                        DD
CFE    Low Intensity Power Mode with DTGS      0
COR    Correlation Test Mode                   0
DEL    Delay Before Measurement                0
DLY    Stabilization Delay                     0
HFW    Wanted High Freq Limit                  15000.0
LFW    Wanted Low Freq Limit                   0.0
NSS    Number of Sample Scans                  50
PLF    Result Spectrum Type                    AB
RES    Resolution (cm-1)                       4.0
SOT    Sample Scans or Time                    0
TCL    Command Line for Additional Data Tr...
TDL    To Do List                              16777271
SGN    Sample Signal Gain                      1

....................................................................................................
                                      Sample Origin Parameters
Key    Label                                   Value
BLD    Building
CNM    Operator Name                           Duran
CPY    Company
DPM    Department
EXP    Experiment                              MWIR-LWIR_Trans_FileNameFormat.XPM
LCT    Location
SFM    Sample Form                             Atm-MWIR (All A)
SNM    Sample Name                             File Test
XPP    Experiment Path                         C:\\Users\\Public\\Documents\\Bruker\\OPUS_8.1.29\\XPM
IST    Instrument Status                       OK
CPG    Character Encoding Code Page            1252
UID    Universally Unique Identifier           0d1348c2-3a2c-41c9-b521-bdaf0a23710c

....................................................................................................
                                    Instrument Status Parameters
Key    Label                                   Value
HFL    High Folding Limit                      15795.820598
LFL    Low Folding Limit                       0.0
LWN    Laser Wavenumber                        15795.820598
ABP    Absolute Peak Pos in Laser*2            52159
SSP    Sample Spacing Divisor                  1
ASG    Actual Signal Gain                      1
ARG    Actual Reference Gain                   1
ASS    Number of Sample Scans                  50
GFW    Number of Good Forward Scans            25
GBW    Number of Good Backward Scans           25
BFW    Number of Bad Forward Scans             0
BBW    Number of Bad Backward Scans            0
PKA    Peak Amplitude                          1409
PKL    Peak Location                           7364
PRA    Backward Peak Amplitude                 1356
PRL    Backward Peak Location                  7363
P2A    Peak Amplitude Channel 2                1
P2L    Peak Location Channel 2                 1
P2R    Backward Peak Amplitude Channel 2       1
P2K    Backward Peak Location Channel 2        1
DAQ    Data Acquisition Status                 0
AG2    Actual Signal Gain Channel 2            1
HUM    Relative Humidity Interferometer        14
SSM    Sample Spacing Multiplier               1
RSN    Running Sample Number                   565
CRR    Correlation Rejection Reason            0
SRT    Start Time (sec)                        1556890484.642
DUR    Duration (sec)                          42.433990478515625
TSC    Scanner Temperature                     27.8
MVD    Max Velocity Deviation                  0.1158025860786438
PRS    Pressure Interferometer (hPa)           1009.9999700000001
AN1    Analog Signal 1                         0.22596596493037535
AN2    Analog Signal 2                         3.459206583321489
VSN    Firmware Version                        2.450 Oct 10 2014
SRN    Instrument Serial Number                1135
CAM    Coaddition Mode                         0
INS    Instrument Type                         VERTEX 80V
FOC    Focal Length                            100.0
RDY    Ready Check                             1

====================================================================================================
                                  Reference Parameters (rf_params)

....................................................................................................
                               Reference Instrument Status Parameters
Key    Label                                   Value
HFL    High Folding Limit                      15795.820598
LFL    Low Folding Limit                       0.0
LWN    Laser Wavenumber                        15795.820598
ABP    Absolute Peak Pos in Laser*2            52159
SSP    Sample Spacing Divisor                  1
ARG    Actual Reference Gain                   1
ASG    Actual Signal Gain                      1
ASS    Number of Sample Scans                  1
GFW    Number of Good Forward Scans            1
GBW    Number of Good Backward Scans           0
BFW    Number of Bad Forward Scans             0
BBW    Number of Bad Backward Scans            0
PKA    Peak Amplitude                          1644
PKL    Peak Location                           7364
PRA    Backward Peak Amplitude                 1
PRL    Backward Peak Location                  -1
P2A    Peak Amplitude Channel 2                1
P2L    Peak Location Channel 2                 1
P2R    Backward Peak Amplitude Channel 2       1
P2K    Backward Peak Location Channel 2        1
DAQ    Data Acquisition Status                 0
AG2    Actual Signal Gain Channel 2            1
HUM    Relative Humidity Interferometer        0
SSM    Sample Spacing Multiplier               1
RSN    Running Sample Number                   5816
CRR    Correlation Rejection Reason            0
SRT    Start Time (sec)                        1556890282.358
DUR    Duration (sec)                          0.7919998168945312
TSC    Scanner Temperature                     27.8
MVD    Max Velocity Deviation                  0.10553144663572311
PRS    Pressure Interferometer (hPa)           2.01999
AN1    Analog Signal 1                         0.22577181458473206
AN2    Analog Signal 2                         4.0960001945495605
VSN    Firmware Version                        2.450 Oct 10 2014
SRN    Instrument Serial Number                1135
CAM    Coaddition Mode                         0
INS    Instrument Type                         VERTEX 80V
FOC    Focal Length                            100.0
RDY    Ready Check                             1
ARS    Number of Reference Scans               1

....................................................................................................
                                    Reference Optical Parameters
Key    Label                                   Value
ACC    Accessory                               TRANS *010A984F
APR    ATR Pressure                            0
APT    Aperture Setting                        1 mm
BMS    Beamsplitter                            KBr-Broadband
DTC    Detector                                RT-DLaTGS [Internal Pos.1]
HPF    High Pass Filter                        0
LPF    Low Pass Filter                         10.0
LPV    Variable Low Pass Filter (cm-1)         4000
OPF    Optical Filter Setting                  Open
PGR    Reference Preamplifier Gain             3
RCH    Reference Measurement Channel           Sample Compartment
RDX    Extended Ready Check                    0
SRC    Source                                  MIR
VEL    Scanner Velocity                        10.0
ADC    External Analog Signals                 0
SON    External Sync                           Off

....................................................................................................
                                  Reference Acquisition Parameters
Key    Label                                   Value
ADT    Additional Data Treatment               0
AQM    Acquisition Mode                        DD
CFE    Low Intensity Power Mode with DTGS      0
COR    Correlation Test Mode                   0
DEL    Delay Before Measurement                0
DLY    Stabilization Delay                     0
HFW    Wanted High Freq Limit                  15000.0
LFW    Wanted Low Freq Limit                   0.0
NSR    Number of Background Scans              1
PLF    Result Spectrum Type                    TR
RES    Resolution (cm-1)                       4.0
RGN    Reference Signal Gain                   1
STR    Scans or Time (Reference)               0
TCL    Command Line for Additional Data Tr...
TDL    To Do List                              16777271

....................................................................................................
                               Reference Fourier Transform Parameters
Key    Label                                   Value
APF    Apodization Function                    B3
HFQ    End Frequency Limit for File            500.0
LFQ    Start Frequency Limit for File          10000.0
NLI    Nonlinearity Correction                 0
PHR    Phase Resolution                        100.0
PHZ    Phase Correction Mode                   ML
SPZ    Stored Phase Mode                       NO
ZFF    Zero Filling Factor                     2
```
</p>
</details>

You can access the sample parameters through the `OPUSFile.params` attribute, or as a direct attribute for shorthand
(e.g. `OPUSFile.params.apt` or `OPUSFile.apt`).  The parameter keys are also case insensitive (e.g. `OPUSFile.bms` or
`OPUSFile.BMS`).

OPUS files can also contain parameter information about the associated reference (aka background) measurement. These
parameters are only accessible through the `OPUSFile.rf_params` attribute to avoid namespace collisions (e.g.
`OPUSFile.rf_params.apt`).

```python
data = read_opus('file.0')
print('Sample ZFF:', data.zff, 'Reference ZFF:', data.rf_params.zff)
```
```console
Sample ZFF: 2 Reference ZFF: 2
```

You can also get the human-readable label for a parameter key using the `get_param_label` function:

```python
from brukeropus.file import get_param_label
data = read_opus('file.0')
print(get_param_label('bms') + ':', data.bms)
print(get_param_label('src') + ':', data.src)
```
```console
Beamsplitter: KBr-Broadband
Source: MIR
```

You can also iterate over the parameters using the familiar `keys()`, `values()`, and `items()` functions using the
`params` or `rf_params` attributes (just like a dictionary):

```python
data = read_opus('file.0')
for key, val in data.params.items():
    print(key + ':', val)
```
```console
acc: TRANS *010A984F
apr: 0
apt: 1 mm
bms: KBr-Broadband
chn: Sample Compartment
dtc: RT-DLaTGS [Internal Pos.1]
hpf: 0
lpf: 10.0
lpv: 4000
opf: Open
pgn: 3
... continued ...
```

###Data and DataSeries (brukeropus.file.data)

Depending on the settings used to save the OPUS file, different data blocks can be stored. These can include phase,
interferograms, single-channel spectra and result spectra (e.g. absorbance, transmittance, etc.). To retrieve a list of
the data blocks stored in the OPUS File, you can use the `all_data_keys` attribute:

```python
data = read_opus('file.0')
print(data.all_data_keys)
```
```console
['igsm', 'phsm', 'sm', 'a', 'igrf', 'rf']
```

Each key is also an attribute of the `OPUSFile` instance that returns either a `Data` (single spectra) or `DataSeries`
(series of spectra) class.  You can use the `data_keys` attribute to retrieve a list of only the single-spectra `Data`
keys in the class, or the `series_keys` attribute to retrieve a list of only the `DataSeries` keys.

You can also iterate over these data keys using the `iter_all_data()`, `iter_data()` and `iter_series()` class
methods:

```python
data = read_opus('file.0')
for d in data.iter_data():
    print(d.label, '(' + d.datetime.isoformat(' ') + ')')
```
```console
Sample Interferogram (2019-05-03 13:34:44.641000)
Sample Phase (2019-05-03 13:34:44.641000)
Sample Spectrum (2019-05-03 13:34:44.641000)
Absorbance (2019-05-03 13:34:44.641000)
Reference Interferogram (2019-05-03 13:31:22.358000)
Reference Spectrum (2019-05-03 13:31:22.358000)
```

You can access the `x` and `y` arrays of a `Data` or `DataSeries` class:

```python
data = read_opus('file.0')
plt.plot(data.a.x, data.a.y)  # Plot absorbance
plt.ylim((0, 1))
plt.show()
```

For spectra with wavenumber as valid unit (e.g. single-channel or result spectra), the `x` array can be given in
wavenumber [`cm⁻¹`], wavelength [`µm`], or modulation frequency [`Hz`] units by using the attributes: `wn`, `wl`, or `f`
respectively:

```python
data = read_opus('file.0')
plt.plot(data.sm.wl, data.sm.y)
plt.show()
```

Each data block in an OPUS file also contains a small parameter block with information such as the min/max y-value
(mny, mxy), x-units (dxu), number of data points (npt), etc.  These can be accessed as direct attributes to the `Data`
class, or through the `Data.params` attribute:

```python
data = read_opus('file.0')
print('Sample spectra y-min:', data.sm.mny, 'y-max:', data.sm.mxy)
```
```console
Sample spectra y-min: 1.2147593224653974e-05 y-max: 0.03543896973133087
```

###Reports (brukeropus.file.report)

OPUS files may also store a variety of reports which typically contain data in tabular format.  Because an OPUS file may
contain multiple reports, they are stored as a `list` in the `reports` attribute (even if only one is available). For
OPUS files with no reports, the `reports` attribute will simply return an empty list.  Reports can be printed to the
console.  As an example of how to access the report data, we will use a Multi-Evaluation Test Report (mev):

```python
data = read_opus(mevfile.0)
print(data.reports[0])
```

```console
====================================================================================================
                                    Multi Evaluation Test Report
____________________________________________________________________________________________________
         Version: 4
     Method Path: C:\\Users\\Public\\Documents\\Bruker\\OPUS_8.9.7\\ME_Base\ME
     Method Name: IPA Water Int Q1 Q2.mev
Method Date Time: 2025/04/03 17:39:01 (GMT-5)


Multi Evaluation Test Report (table): cols: 6, rows: 4
----------------------------------------------------------------------------------------------------
       Type: Q2  Q2  INT  INT  Q1  Q1
  Subreport: 1   1   2    2    3   3
        Row: 1   2   1    2    1   2
Last Change: 0   0   0    0    0   0
----------------------------------------------------------------------------------------------------
Subreport 0
Quant 2 (table): cols: 2, rows: 35
----------------------------------------------------------------------------------------------------
                  Method_Path: C:\\Users\\Public\\Docume...  C:\\Users\\Public\\Docume...
                  Method_Name: IPA Method.q2              H2O Method.q2
             Date_Time_Method: 2025/04/03 11:50:33 (G...  2025/04/03 11:47:05 (G...
           Date_Time_Analysis: 2025/04/03 21:26:08 (G...  2025/04/03 21:26:09 (G...
                 X_Startpoint: 8920                       9900
                   X_Endpoint: 5396                       6028
               Component_Name: IPA                        H2O
               Component_Unit: %                          %
          Component_Name_User: IPA                        H2O
          Component_Unit_User: %                          %
                   Formatting: %.5G                       %.5G
                   Prediction: -0.0157854                 100.162
           Prediction_Outside: 1                          1
        Prediction_Calculated: -0.0157854                 100.162
Prediction_Calculated_Outside: 0                          0
                      Formula:
                External_Bias: 3.40282e+38                3.40282e+38
         Target_Concentration: 3.40282e+38                3.40282e+38
          Warning_Upper_Limit: 3.40282e+38                3.40282e+38
          Warning_Lower_Limit: 3.40282e+38                3.40282e+38
            Alarm_Upper_Limit: 3.40282e+38                3.40282e+38
            Alarm_Lower_Limit: 3.40282e+38                3.40282e+38
                     Mah_Dist: 0.281401                   0.330205
               Mah_Dist_Limit: 0.569619                   0.717409
     Mah_Dist_Limit_By_Factor: 0.569619                   0.717409
             Mah_Dist_Outlier: 0                          0
                          MDI: 0.494015                   0.460275
                Spec_Residual: 0.000657344                0.000157652
                      F_Value: 1.78523                    0.977421
                       F_Prob: 0.801844                   0.664059
                 F_Prob_Limit: 0.99                       0.99
        Spec_Residual_Outlier: 0                          0
      Component_Value_Density: 3.40282e+38                3.40282e+38
Component_Value_Density_Limit: 3.40282e+38                3.40282e+38
         Process_Channel_Name:
----------------------------------------------------------------------------------------------------
Subreport 1
Integration (table): cols: 2, rows: 25
----------------------------------------------------------------------------------------------------
                  Method_Path: C:\\Users\\Public\\Docume...  C:\\Users\\Public\\Docume...
                  Method_Name: Water Integration.int      IPA Integration.int
             Date_Time_Method: 2025/04/03 12:49:06 (G...  2025/04/03 12:45:18 (G...
           Date_Time_Analysis: 2025/04/03 21:26:09 (G...  2025/04/03 21:26:09 (G...
                 X_Startpoint: 8127.6                     5970.95
                   X_Endpoint: 7368.4                     5874.2
                        Label: H2O                        IPA
                   Label_User: H2O                        IPA
                         Type: B                          B
                   Formatting: %.6G                       %.6G
           Integration_Result: -155.238                   -0.918539
Integration_Result_Calculated: -155.238                   -0.918539
                      Formula:
                       Freq_1: 8127.6                     5970.95
                       Freq_2: 7368.4                     5874.2
                       Freq_3: 1.001e-199                 1.001e-199
                       Freq_4: 1.001e-199                 1.001e-199
                       Freq_5: 1.001e-199                 1.001e-199
                       Freq_6: 1.001e-199                 1.001e-199
         Target_Concentration: 3.40282e+38                3.40282e+38
          Warning_Upper_Limit: 3.40282e+38                3.40282e+38
          Warning_Lower_Limit: 3.40282e+38                3.40282e+38
            Alarm_Upper_Limit: 3.40282e+38                3.40282e+38
            Alarm_Lower_Limit: 3.40282e+38                3.40282e+38
         Process_Channel_Name:
----------------------------------------------------------------------------------------------------
Subreport 2
Quant 1 (table): cols: 2, rows: 22
----------------------------------------------------------------------------------------------------
          Method_Path: C:\\Users\\Public\\Docume...  C:\\Users\\Public\\Docume...
          Method_Name: Water Quant 1_Linear.q1    IPA Quant 1_Linear.q1
     Date_Time_Method: 2025/04/03 12:48:16 (G...  2025/04/03 09:03:49 (G...
   Date_Time_Analysis: 2025/04/03 21:26:09 (G...  2025/04/03 21:26:09 (G...
         X_Startpoint: 7368.4                     5874.2
           X_Endpoint: 8127.6                     5970.95
       Component_Name: Water                      IPA
       Component_Unit: %                          %
  Component_Name_User: Water                      IPA
  Component_Unit_User: %                          %
           Formatting: %.4G                       %.4G
           Prediction: 86.3654                    -7.54551
Prediction_Calculated: 86.3654                    -7.54551
              Formula:
                Sigma: 9.65275                    10.7219
   Integration_Result: 159.336                    135.308
 Target_Concentration: 3.40282e+38                3.40282e+38
  Warning_Upper_Limit: 3.40282e+38                3.40282e+38
  Warning_Lower_Limit: 3.40282e+38                3.40282e+38
    Alarm_Upper_Limit: 3.40282e+38                3.40282e+38
    Alarm_Lower_Limit: 3.40282e+38                3.40282e+38
 Process_Channel_Name:
----------------------------------------------------------------------------------------------------
====================================================================================================
```

At the very top of the report, you see a centered title.  This title can be accessed by the `title`
attribute of the `Report`.

```python
report = data.reports[0]
print(report.title)
```
```console
Multi Evaluation Test Report
```

After the title, you see a list of report properties.  These properties are stored as a `dict` in
the `properties` attribute of a `Report`, but can also be accessed by indexing the report using the
property key (case insensitive):
```python
for key, val in report.properties.items():
    print(key, val)
print('\\nAccessing report properties by name:')
print(report['Method Name'], report['Method Name'] == report['method name'])
```
```console
Version 4
Method Path C:\\Users\\Public\\Documents\\Bruker\\OPUS_8.9.7\\ME_Base\\ME
Method Name IPA Water Int Q1 Q2.mev
Method Date Time 2025/04/03 17:39:01 (GMT-5)

Accessing report properties by name:
IPA Water Int Q1 Q2.mev True
```

Following the report properties is a table.  This data is stored in the `table` attribute of a 
`Report` as a `ReportTable` class (`brukeropus.file.report.ReportTable`).  `ReportTable`s have
titles, headers, and values.  Below is a snippet showing how to access data from the report table:

```python
print('Table title:', report.table.title)
print('Table Headers:', report.table.header)
print('Table row values by name:', report.table['Type'])
print('Table row values by index:', report.table[1])
print('Last value of a table row:', report.table['Type'][-1])
```
```console
Table title: Multi Evaluation Test Report
Table Headers: ['Type', 'Subreport', 'Row', 'Last Change']
Table row values by name: ['Q2', 'Q2', 'INT', 'INT', 'Q1', 'Q1']
Table row values by index: [1, 1, 2, 2, 3, 3]
Last value of a table row: Q1
```

In this report, the table is followed by a series of subreports.  Because a report can have multiple
subreports (this file has 3), they are stored as a `list` in the `sub` attribute of a `Report`.
Subreports can be accessed by indexing the `sub` attribute, or directly indexing the `Report`.
Because these subreports are `ReportTable`s, they have the same interface as above:

```python
print('First subreport title:', report.sub[0].title)
print('Second subreport title:', report[1].title)
print('First subreport Method Names:', report[0]['method_name'])
print('First method name of the first subreport:', report[0]['method_name'][0])
```
```console
First subreport title: Quant 2
Second subreport title: Integration
First subreport Method Names: ['IPA Method.q2', 'H2O Method.q2']
First method name of the first subreport: IPA Method.q2
```
'''

from brukeropus.file.block import *
from brukeropus.file.constants import *
from brukeropus.file.data import *
from brukeropus.file.directory import *
from brukeropus.file.file import *
from brukeropus.file.labels import *
from brukeropus.file.params import *
from brukeropus.file.parse import *
from brukeropus.file.report import *
from brukeropus.file.utils import *

