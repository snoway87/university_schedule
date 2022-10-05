import sys
import csv
import re
import datetime
from time import sleep
from  icalendar import Calendar, Event, Alarm

class Schedule:
    def __init__(self, csv_file, except_classes, end_date="2022-12-30"):
        self.csv_file = csv_file.strip().lower()
        self.except_classes = [c.strip().lower() for c in except_classes]
        self.shedule = []
        self.current_week_number = datetime.date.today().isocalendar()[1] - datetime.date(datetime.datetime.now().year, 9, 1).isocalendar()[1]
        self.end_week_number = self.get_week_number_by_date(end_date)
        assert self.end_week_number > self.current_week_number

    def get_week_number_by_date(sekf, date_string):
        date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return date.isocalendar()[1] - datetime.date(datetime.datetime.now().year, 9, 1).isocalendar()[1]

    def get_university_datetime(self, week_number, week_day = "Mon", hours = "00", minutes = "00"):
        week_number -= 1
        week_diff = week_number - self.current_week_number if week_number >= self.current_week_number else (self.current_week_number - week_number) * -1
        condition = "{:d}-W{:d}".format(datetime.datetime.now().year, datetime.date.today().isocalendar()[1] + week_diff)
        return datetime.datetime.strptime(condition + "-" + week_day + "-" + hours + "-" + minutes, "%Y-W%W-%a-%H-%M")

    def get_class_weeks(self, class_name, is_even_week = True):
        except_for = re.search("^кр.", class_name)
        pairs = re.findall("\d{1,2}\s*[-]\s*\d{1,2}", class_name)
        weeks = re.findall("\d{1,2}", class_name)

        for pair in pairs:
            pair = pair.split("-")
            for week in range(int(pair[0]) + 1, int(pair[1])):
                if is_even_week == True and week % 2 == 0:
                    weeks.append(week)
                if is_even_week == False and week % 2 != 0:
                    weeks.append(week)

        except_weeks = []
        if except_for:
            for week in range(1, self.end_week_number + 2):
                if is_even_week == True and week % 2 == 0 and not str(week) in weeks:
                    except_weeks.append(week)
                if is_even_week == False and week % 2 != 0 and not str(week) in weeks:
                    except_weeks.append(week)
            return sorted([int(i) for i in except_weeks])

        if len(weeks) == 0:
            for week in range(1, self.end_week_number + 2):
                if is_even_week == True and week % 2 == 0:
                    weeks.append(week)
                if is_even_week == False and week % 2 != 0:
                    weeks.append(week)

        return sorted([int(i) for i in weeks])

    def skip_class(self, checking_class):
        checking_class = checking_class.strip().lower()
        found = False
        for except_class in self.except_classes:
            if checking_class.find(except_class) < 0:
                continue
            else:
                found = True
                break
        return found

    def convert_to_ics(self):
        #date = self.get_university_datetime(6, "Sat")
        with open(self.csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            calendar = Calendar()
            calendar.add('prodid', '-//MIREA Calendar//mirea.ru//')
            calendar.add('version', '2.0')

            current_day = 0
            class_count = 1
            time_start = ""
            time_end = ""
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            for idx, row in enumerate(csv_reader):
                if idx % 2 == 0:
                    class_count = int(row[0])
                    time_start = row[1]
                    time_end = row[2]

                # Make an event
                class_name = row[4]
                if  class_name != "" and not self.skip_class(class_name):
                    year = datetime.datetime.now().year
                    day = days[ current_day ]
                    is_even_week = True if row[3] == 'II' else False
                    class_type = row[5]
                    teacher_name = row[6]
                    class_room = row[7]

                    # Get class weeks
                    class_weeks = self.get_class_weeks(class_name, is_even_week)
                    def first_upper(string):
                        for i, ch in enumerate(string):
                            if string[i].isupper():
                                return i
                        return 0

                    for week in class_weeks:
                        sleep(0.01)
                        event = Event()

                        class_name = class_name[first_upper(class_name):]
                        summary =  class_type + ' - ' + class_name if class_type != "" else class_name
                        event.add('summary', summary)

                        start_date = self.get_university_datetime(week, day, time_start.split("-")[0], time_start.split("-")[1])
                        end_date = self.get_university_datetime(week, day, time_end.split("-")[0], time_end.split("-")[1])
                        event.add('description', teacher_name + ', ' + class_room)
                        event.add('dtstart', start_date)
                        event.add('dtend', end_date)

                        # Alert
                        alarm = Alarm()
                        alarm['uid'] = datetime.datetime.now()
                        alarm.add('trigger', datetime.timedelta(minutes=-30))
                        alarm.add('action', 'AUDIO')
                        event.add_component(alarm)
                        calendar.add_component(event)

                # Change day
                if idx % 2 != 0 and class_count == 7:
                    current_day += 1

            ics_file = open(self.csv_file.replace(".csv", ".ics"), 'wb')
            ics_file.write(calendar.to_ical())
            ics_file.close()


if __name__ == '__main__':
    csv_file = sys.argv[1]
    end_date = sys.argv[2]

    schedule = Schedule(csv_file, except_classes = [
        'Информационные измерительные и управляющие системы',
        'Средства сквозного проектирования интеллектуальных измерительных  приборов',
        'Спектральные и поляризационные приборы',
        'Измерительные оптико-электронные приборные комплексы'
    ], end_date = end_date)
    schedule.convert_to_ics()
