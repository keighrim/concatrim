# Concatrim

Concatrim is a python program to trim-and-concatenate media files. It depends on [`ffmpeg`](https://www.ffmpeg.org/).

## License 

Concatrim is distributed as source code on this repository and PyPI under [MIT](LICENSE) license.

## Features

1. Trim an input time-based media file based on given time spans and concatenate trimmed pieces into a single file.
1. Mapping between time points in the original and trimmed file. 

## Installation 

### Dependencies

#### System application

* [`ffmpeg`](https://www.ffmpeg.org/)

#### Python libraries

See [requirements.txt](requirements.txt).

### From PyPI

Install using `pip`

``` bash 
pip install concatrim
```

### From source

Clone this repository and run `setup.py` to install

``` bash
python setup.py install
```

### Usage 

#### Caveats 
At the moment; 
* the package only provides Python API's for its supported operations (no command line interface).
* the program only supports audio inputs. 


#### trim-then-concatenate

To trim a media file, use `Concatrimmer` class from `concatrim` package. 
Initiate an instance with the input file name and optionally configuration for padding. When you trim more than two parts of the input media, a silence padding (configured in milliseconds) will be inserted between each slice. 

``` python
from concatrim import Concatrimmer

c = Concatrimmer('input-file.mp3', 1000)  # will insert 1-second silences between slices
```

From here, you can set which part of the input we want to trim, using `add_spans` method. 

```python
c.add_spans([1000, 4000], [12000, 22000])
#  configures the program to extract two parts, 1-4 second and 12-22 second. 
```

When you're done adding spans, call `concatrim` method, with a directory name you want to use to store trimmed output file. 

```python
c.concatrim('../outputs')
```

Additionally, we can pass `prefix`, `suffix` arguments to rename the output file (`suffix` will be added at before the extension name).

```python
c.concatrim('../outputs', suffix='.trimmmed')
```

#### Timepoint conversion

Once you have all spans for trimming configured in a `Concatrimmer` object, you can also ask for conversion between two time points; one from the original media file, and the other from the trimmed one. This conversion will consider the padding pauses that'd be inserted between spans. Again, all input and output of the conversion is in milliseconds. 

```python 
c.conv_to_trimmed(2100)  # will return 1100
c.conv_to_original(1100)  # will return 2100
c.conv_to_original(11100)  # will return None because 11100 ms is trimmed out
c.conv_to_original(12100)  # will return 4100
```