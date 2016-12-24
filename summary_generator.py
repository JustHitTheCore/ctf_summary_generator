"""
Downloads spreadsheet from Google Drive/Google API using gspread Python module:
http://gspread.readthedocs.io/

Then it generates a summary about CTF players.
"""
from __future__ import print_function, unicode_literals

from collections import OrderedDict

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

key_path = './credentials/googlesheet_key.json'
scope = ['https://spreadsheets.google.com/feeds']

# We assume that the spreadsheet looks like this:
#     A       |     B      |    C   |    D     |       E         |   F    |      G      |
# ------------|------------|--------|----------|-----------------|--------|-------------|-------
# <ctf name>  |            |        |          |                 |        |             |
# Task        | Kategoria  | Punkty | Zrobione | Kto rozwiazuje  | Flaga  | Krotki opis | Uwagi
# ------------|------------|--------|----------|-----------------|--------|-------------|-------
# <task name> | <category> |  <pts> |    [Y]   |[nick1] [,nick2] | <flag> | <desc>      |
#

is_done = u'Zrobione'
done_by = u'Kto rozwiązuje'
points = u'Punkty'
task = u'Task'
category = u'Kategoria'


def make_summary(sheet_key):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
    google_api = gspread.authorize(credentials)

    tasks_sheet = google_api.open_by_key(sheet_key).sheet1

    # We need to remove the first row, and take CTF name from it.
    # ctf_name = tasks_sheet.acell('A1').value
    data_frame = pd.DataFrame(tasks_sheet.get_all_records(head=2))
    df = data_frame[data_frame[is_done].isin(('Y', 'y'))]

    total_pts = df[points].sum()
    nick_points = df.groupby([done_by])[points].sum()

    ordered_data = OrderedDict(
        ((nick, {'total_points': total_pts, 'tasks': df[df[done_by] == nick]}) for nick, total_pts in nick_points.items())
    )

    return total_pts, ordered_data


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: %s <sheet_key>" % sys.argv[0])
        exit(0)

    sheet_key = sys.argv[1]

    total_points, summary_data = make_summary(sheet_key)

    print("Zdobyte punkty - {}:".format(total_points))
    for nick, d in summary_data.items():
        print('- {nick}: {pts}'.format(nick=nick, pts=d['total_points']))
        for idx, row in d['tasks'].iterrows():
            print('    {category} - {task}: {points}'.format(task=row[task], category=row[category], points=row[points]))
