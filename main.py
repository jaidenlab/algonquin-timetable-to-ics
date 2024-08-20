import logging
import icalendar # pip install icalendar
import re
import datetime
import pytz
import uuid

# Module level dunders
__version__ = "1.0"

logger = logging.getLogger(__name__)

class Timetable:
    def __init__(self) -> None:
        self.tz = pytz.timezone('America/Toronto')
        self.calendar = icalendar.Calendar()
        self.course_names = {} # original name, final name

        # Product Identifier https://www.kanzaki.com/docs/ical/prodid.html
        self.calendar.add("PRODID", "Algonquin timetable to .ics")
        self.calendar.add("VERSION", "2.0") # iCalendar spec version

        # TODO: Document this better
        # Create timezone for America/Toronto
        timezone = icalendar.Timezone()
        timezone.add('TZID', 'America/Toronto')
        
        # TODO: Use pytz timezone to get this information?
        # EDT timezone info
        daylight_timezone = icalendar.TimezoneDaylight()
        daylight_timezone.add('TZOFFSETFROM', datetime.timedelta(hours=-5))
        daylight_timezone.add('TZOFFSETTO', datetime.timedelta(hours=-4))
        daylight_timezone.add('TZNAME', 'EDT')
        daylight_timezone.add('DTSTART', datetime.datetime(1970, 3, 8))
        daylight_timezone.add('RRULE', {'FREQ': 'YEARLY', 'BYMONTH': 3, 'BYDAY': '2SU'})

        # EST timezone info
        standard_timezone = icalendar.TimezoneStandard()
        standard_timezone.add('TZOFFSETFROM', datetime.timedelta(hours=-4))
        standard_timezone.add('TZOFFSETTO', datetime.timedelta(hours=-5))
        standard_timezone.add('TZNAME', 'EST')
        standard_timezone.add('DTSTART', datetime.datetime(1970, 11, 1))
        standard_timezone.add('RRULE', {'FREQ': 'YEARLY', 'BYMONTH': 11, 'BYDAY': '1SU'})

        # Combine
        timezone.add_component(daylight_timezone)
        timezone.add_component(standard_timezone)
        self.calendar.add_component(timezone)

    def addCourse(self, str) -> None:
        """Add course event from paragraph"""
        logger.debug(f"Parsing paragraph: {str}")

        match = re.search(r"""
            Course\sName.\s(?P<name>.+?)\s+ # Course name
            Course\sCode.\s(?P<code>.+?)\s+ # Course code
            Section.\s(?P<section>.+?)\s+ # Section # (300)
            Delivery.\s(?P<delivery>.+?)\s+ # Delivery method (Theory/Lab)
            Professor.\s(?P<professor>.+?)\s+ # Professor
            Room\sNumber.\sLocation.\s(?P<room>.+?),\s(?P<campus>.+?)\s+ # Room #, Campus name (Woodroffe)
            Day\sof\sClass.\s(?P<day>.+?)\s+ # Day class takes place (Monday)
            Time:\s(?P<start_time>.+?)\suntil\s(?P<end_time>.+?)\s+ # Time class starts and ends (14:00, 16:30)
            Start\sDate:\s(?P<start_date>.+?)\s+ # Date first class takes place (06-May-2024)
            End\sDate:\s(?P<end_date>.+?)\s+ # Date last class takes place (05-Aug-2024)
            Academic\sPenalty\sWithdrawal\sDate:\s(?P<penalty_date>.+)\s* # Final penalty-free withdrawal date
        """, str, re.VERBOSE)

        if match == None:
            raise ValueError("Unknown course format", str)
        
        groups = match.groupdict()

        # Log all groups
        logger.debug(groups)

        # Format for dates and times in the paragraph
        DATE_FORMAT = '%d-%b-%Y'
        TIME_FORMAT = '%H:%M'

        start_time_str = groups['start_time']
        end_time_str = groups['end_time']
        start_date_str = groups['start_date']
        end_date_str = groups['end_date']
        room = groups['room']
        name = groups['name']
        delivery = groups['delivery']
        weekday = groups['day']

        # Convert strings to dates and times
        class_date = datetime.datetime.strptime(start_date_str, DATE_FORMAT).date()
        class_start_time = datetime.datetime.strptime(start_time_str, TIME_FORMAT).time()
        class_end_time = datetime.datetime.strptime(end_time_str, TIME_FORMAT).time()
        # Add an extra day to avoid bug where last class is not added to calendar
        course_expiry = datetime.datetime.strptime(end_date_str, DATE_FORMAT).date() + datetime.timedelta(days=1)

        dtstart = datetime.datetime.combine(class_date, class_start_time, tzinfo=self.tz)
        dtend = datetime.datetime.combine(class_date, class_end_time, tzinfo=self.tz)
        dtstamp = datetime.datetime.now(tz=self.tz)

        # Optionally replace course names with friendlier versions
        new_name = self.course_names.get(name) or input(f'"{name}"? ').strip() or name
        self.course_names.update({name: new_name}) # Remember choice for duplicate course names (Ex: Theory/Lab)

        # Name to use in calendar event
        event_name = f'{room} {new_name} ({delivery})'

        # Create iCalendar event
        event = icalendar.Event()
        event.add('SUMMARY', event_name)
        event.add('DTSTART', dtstart)
        event.add('DTEND', dtend)
        event.add('DTSTAMP', dtstamp)
        event.add('UID', uuid.uuid4())
        event.add('RRULE', {'FREQ': 'WEEKLY', 'UNTIL': course_expiry, 'BYDAY': weekday[:2]})

        # Log event in ical format
        logger.debug(event.to_ical())

        # Add event to calendar
        self.calendar.add_component(event)

    def loadFile(self, filepath) -> None:
        with open(filepath, 'r', encoding='UTF-8') as file:
            # Split the text into paragraphs
            current_paragraph = ''
            for line in file:
                if line == '\n':
                    if current_paragraph:
                        self.addCourse(current_paragraph)
                        current_paragraph = ''
                    continue
                current_paragraph += line

            # No newline at end of file, still parse the data
            if current_paragraph:
                self.addCourse(current_paragraph)

    def saveFile(self, filepath) -> None:
        with open(filepath, 'wb') as file:
            file.write(self.calendar.to_ical())
            logger.debug(f'Calendar written to: {filepath}')

def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="Algonquin timetable to .ics",
        description="Converts a .rtf file to a .ics file",
        epilog="Written by Jaiden L"
    )

    # Version information
    parser.add_argument("-V", "--version", action="version", version="%(prog)s {version}".format(version=__version__))

    # File paths
    parser.add_argument("input", help="Path to .rtf file")
    parser.add_argument("output", help="Path to save .ics file")

    # inputFilename = args.input or filedialog.askopenfile(filetypes=[("Rich Text Format", ".rtf")])
    # outputFilename = args.output or filedialog.asksaveasfile(filetypes=[("iCalendar file", ".ics")])
    
    # Logging level (default: WARNING)
    parser.add_argument("-v", "--verbose", help="Set logging level to INFO", action="store_const", dest="loglevel", const=logging.INFO, default=logging.WARNING)
    parser.add_argument("-d", "--debug", help="Set logging level to DEBUG", action="store_const", dest="loglevel", const=logging.DEBUG)
    
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    timetable = Timetable()
    try:
        timetable.loadFile(args.input)
    except IOError as e:
        logger.error("Failed to load input file")
        raise

    try:
        timetable.saveFile(args.output)
    except IOError as e:
        logger.error("Failed to save output file")
        raise

if __name__ == "__main__":
    main()
