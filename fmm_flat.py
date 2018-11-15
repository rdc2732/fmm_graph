# fmm_flat.py
# This program will convert the FMM.csv file which has multiple dependencies on one line, to a different
# format with one keyword/dependency per row.  This will lend the data to be more easily analyzed with
# Excel and pivot tables.

import re
import csv
import glob

# Define files
csvfile = 'FMM.csv'
csvout = 'FMM-out.csv'

# CSV records; rec[0] = FM Keyword; rec[1] = list of FM Dependencies
with open(csvfile) as csv_file:
    with open(csvout, 'w', newline='') as csv_out:
        csv_reader = csv.reader(csv_file, delimiter=',')
        csv_writer = csv.writer(csv_out, delimiter=',')
        line_count = 0
        for row in csv_reader:
            dependency_list = row[4].split(';')
            while '' in dependency_list: # Remove unfortunate trailing '' elements
                dependency_list.remove('')
            for dependency in dependency_list:
                new_row = row
                row[4] = dependency
                csv_writer.writerow(new_row)
            line_count += 1
        print(f'Processed {line_count} lines.')

