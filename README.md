# algonquin-timetable-to-ics
Convert an Algonquin College timetable stored as .rtf to an iCalendar .ics file.

## Getting Started

A python3 environment is required to run this script

### Prerequisites

1. Install Python version >= 3.0 from [https://www.python.org](https://www.python.org/downloads/)
2. Install required modules
```
pip install -r /path/to/requirements.txt
```

## Usage

The python script `main.py` should be ran from the command line like so
```
python /path/to/main.py [-h] [-V] [-v] [-d] /path/to/input.rtf /path/to/output.ics
```

There are a few arguments available
```
positional arguments:
  input          Path to .rtf file
  output         Path to save .ics file

options:
  -h, --help     show this help message and exit
  -V, --version  show program's version number and exit
  -v, --verbose  Set logging level to INFO
  -d, --debug    Set logging level to DEBUG
```

