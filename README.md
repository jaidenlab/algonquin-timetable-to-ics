# algonquin-timetable-to-ics
Convert an Algonquin College timetable stored as .rtf to an iCalendar .ics file.

> [!WARNING]
> This program ignores holidays and breaks. Class events must manually be removed for those days. 

## Getting Started

A python3 environment is required to run this script

### Prerequisites

1. Install Python version >= 3.0 from [https://www.python.org](https://www.python.org/downloads/)
2. Install required modules
```
pip install -r /path/to/requirements.txt
```

### Obtaining the .rtf file
1. Login to [ACSIS](https://acsis.algonquincollege.com/students/).
2. Go to **View TimeTable** under **Courses**.
3. Click the **Export to RTF** button.  
![image](https://github.com/user-attachments/assets/280e3a94-5ef6-4429-a8df-e95acdc8a41e)


## Usage

The python script `main.py` should be ran from the command line like so
```
python /path/to/main.py [-h] [-V] [-v] [-d] input.rtf output.ics
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
## Importing .ics file into another program
The ICS format is a universal calendar file format that all popular calendar applications support.  
Examples include but are not limited to:
- Microsoft Outlook
- Google Calendar
- Apple Calendar

### Google Calendar
1. Open google calendar and click the ➕ next to **Other calendars**.  
![image](https://github.com/user-attachments/assets/f8828535-62d9-4366-8917-ffbf440281c5)
2. Click the **import** button from the dropdown menu.  
![image](https://github.com/user-attachments/assets/fc457568-ed1d-4a08-a0e9-25a9264a6ba9)
3. Choose the calendar you wish to add the timetable to and click the **Select file from your computer** button.  
![image](https://github.com/user-attachments/assets/9151034a-2903-43af-937b-4d8bf4147d1c)



