import asyncio
import json

from bs4 import BeautifulSoup
from httpx import Response, AsyncClient

client = AsyncClient()
base_url = "http://www.isarchimede.edu.it/Orario"


async def _get(path: str) -> Response:
    return await client.get(base_url + path)


async def summary() -> dict:
    document = (await _get("/index.html")).content
    soup = BeautifulSoup(document, "lxml")
    table = soup.find('table')

    sections = table.find_all('td')
    data = {}

    for section in sections:
        d = [t for t in section.text.split('\n') if t != '']
        data[d[0]] = []

        for i in range(1, len(d)):
            if d[i].strip() != '':
                data[d[0]].append(d[i])

    return data


def parse_lesson_time_cell(cell):
    return next(iter(cell.find_all('p'))).text.strip()


def parse_days_heading(row):
    cols = iter(row.findAll('td'))
    next(cols)

    days = []
    for cell in cols:
        days.append(cell.text.strip())

    return days


def parse_lesson_cell_classes(cell):
    cell_data = [c for c in cell.findAll('p') if c.text.strip() != '']

    # this is an empty cell
    if len(cell_data) == 0:
        return None

    subject = cell_data[0].text.strip()
    teachers = cell_data[1].text.strip().split(' - ')
    room = cell_data[2].text.strip()

    return {
        'subject': subject,
        'teachers': teachers,
        'room': room
    }


def parse_lesson_cell_teacher(cell):
    cell_data = [c for c in cell.findAll('p') if c.text.strip() != '']

    if len(cell_data) == 0:
        return None

    classs = cell_data[0].text.strip()
    room = cell_data[-1].text.strip()

    if classs == 'Ricevimento Parenti' or classs == 'Progetti':
        return {
            'subject': classs,
            'teachers': [],
            'room': room if room != classs else None
        }

    subject = cell_data[1].text.strip()

    if len(cell_data) >= 4:
        teachers = cell_data[2].text.strip().split(' - ')
    else:
        teachers = []

    return {
        'class': classs,
        'subject': subject,
        'teachers': teachers,
        'room': room
    }


def parse_lesson_cell_room(cell):
    cell_data = cell.find_all('p')
    classs = cell_data[0].text.strip()
    teachers = cell_data[1].text.strip().split(' - ')
    subject = cell_data[2].text.strip()

    return {
        'subject': subject,
        'teachers': teachers,
        'class': classs
    }


async def table(section: str, path: str) -> dict:
    method = parse_lesson_cell_classes

    if section == 'Aule':
        method = parse_lesson_cell_room
    elif section == 'Docenti':
        method = parse_lesson_cell_teacher

    document = (await _get("/" + section.lower().capitalize() + "/" + path + ".html")).content
    soup = BeautifulSoup(document, "lxml")
    table = soup.find('table')

    rows = iter(table.find_all('tr'))

    days_heading = next(rows)
    days = parse_days_heading(days_heading)

    timesheet = [[] for _ in range(len(days))]
    lesson_times = []

    for time_idx, row in enumerate(rows):
        cols = iter(row.findAll('td'))

        # the first column should be the time
        lesson_time = parse_lesson_time_cell(next(cols))
        lesson_times.append(lesson_time)

        day_idx = 0
        for cell in cols:
            # update the day index
            while day_idx < len(days) and len(timesheet[day_idx]) > time_idx:
                day_idx += 1

            # get the rowspan from the cell
            lesson_duration = int(cell['rowspan'])
            # this should not fail, in case it does the logic needs to be rebuilt

            lesson_data = method(cell)
            for _ in range(lesson_duration):
                timesheet[day_idx].append(lesson_data)

    data = {}

    for day, lessons in zip(days, timesheet):
        data[day] = {}
        for lesson_time, lesson in zip(lesson_times, lessons):
            data[day][lesson_time] = lesson

    print(json.dumps(data, indent=4))
    return data


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(table('Aule', 'Aula 18'))
