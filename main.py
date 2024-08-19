import logging
import icalendar
import datetime
import re
import pytz

logger = logging.getLogger(__name__)
logging.basicConfig(filename='debug.log', filemode='w', level=logging.DEBUG)

# Paste paths to .ics and .rtf file here
TIMETABLE_FILEPATH = ''
ICS_FILEPATH = ''

class ScheduleConverter():
    def __init__(self) -> None:
        self.tz = pytz.timezone('America/Toronto')
        self.__init_calendar()
        self.course_name_replacements = {} # old name, new name
        self.existing_uids = [] # List of existing uids just in case
    
    def __init_calendar(self) -> None:
        self.calendar = icalendar.Calendar()

        # TODO: Explain this
        # Necessary fields to make the calendar work
        self.calendar.add('PRODID', '-//My calendar product//mxm.dk//')
        self.calendar.add('VERSION', '2.0')

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

    def __generate_uid(self) -> str:
        while True:
            uid = f'{datetime.datetime.now()}@unique.id'
            if uid not in self.existing_uids:
                self.existing_uids.append(uid) # Add UID to list of existing UIDs
                return uid
            else:
                logger.warning('UID already exists')

    def addCourseFromParagraph(self, paragraph) -> None:
        logger.debug(f'Parsing paragraph: {paragraph}')

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
        """, paragraph, re.VERBOSE)

        if match == None:
            logger.error(f'Unknown course format: {paragraph}')
            return
        
        groups = match.groupdict()

        # Log all groups for easy debugging
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
        new_name = self.course_name_replacements.get(name) or input(f'"{name}"? ').strip() or name
        self.course_name_replacements.update({name: new_name}) # Remember choice for duplicate course names (Ex: Theory/Lab)

        # Name to use in calendar event
        event_name = f'{room} {new_name} ({delivery})'

        # Create iCalendar event
        event = icalendar.Event()
        event.add('SUMMARY', event_name)
        event.add('DTSTART', dtstart)
        event.add('DTEND', dtend)
        event.add('DTSTAMP', dtstamp)
        event.add('UID', self.__generate_uid())
        event.add('RRULE', {'FREQ': 'WEEKLY', 'UNTIL': course_expiry, 'BYDAY': weekday[:2]})

        # Log event in ical format
        logger.debug(event.to_ical())

        # Add event to calendar
        self.calendar.add_component(event)

    def loadTimetableFile(self, filepath) -> None:
        with open(filepath, 'r', encoding='UTF-8') as file:
            # Split the text into paragraphs
            current_paragraph = ''
            for line in file:
                if line == '\n':
                    if current_paragraph:
                        self.addCourseFromParagraph(current_paragraph)
                        current_paragraph = ''
                    continue
                current_paragraph += line

            # No newline at end of file, still parse the data
            if current_paragraph:
                self.addCourseFromParagraph(current_paragraph)

    def outputiCalFile(self, filepath) -> None:
        with open(filepath, 'wb') as file:
            file.write(self.calendar.to_ical())
            logger.debug(f'Calendar written to: {filepath}')


def main():
    logger.debug('main function entered')
    converter = ScheduleConverter()
    converter.loadTimetableFile(TIMETABLE_FILEPATH)
    converter.outputiCalFile(ICS_FILEPATH)
    logger.debug('main function finished')


if __name__ == '__main__':
    main()









