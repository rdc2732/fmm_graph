# fmm_graph.py
# This program will loop through a CSV file exported from the DOORS FMM module.  Each line of the file
# contains a FMM keyword.  Many of the keywords are dependent upon other keywords.  This program will
# parse the file and extract all keywords, and build a directed graph that shows all dependencies.
#
# The program will output a .gfz file to allow Graphiz to build a directed graph of the signals and modules.
# Sqlite will be used to store the  keywords, and then queried to create the data sets for the .gfx.
#
# Parsing the FMM.csv file:
#   - Column headings (import columns marked with *):
#       FM Selection GUI tab
#       Function
#       Selectable Options
#       FM Selection*
#       FM Selection Dependencies*
#       Rule Type
#       Selection Min
#       Selection Max

import re
import csv
import glob
import sqlite3

# Define files
sqldbfile = 'FMM.db'
csvfile = 'FMM.csv'
dotfile = 'FMM.gfz'


# Set up sqlite database
con = sqlite3.connect(sqldbfile)
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS Keywords")
cur.execute("DROP TABLE IF EXISTS KeyDepends")
cur.execute("CREATE TABLE Keywords (key_id INTEGER PRIMARY KEY, keyword TEXT, UNIQUE (keyword))")
cur.execute("CREATE TABLE KeyDepends (depon INTEGER, depto INTEGER, \
                FOREIGN KEY (depon) REFERENCES Keywords(key_id), \
                FOREIGN KEY (depto) REFERENCES Keywords(key_id))")


sql_query = \
    """select 
        k1.keyword as Dependency, 
        k2.keyword as Dependent 
    from 
        Keywords as k1,
        Keywords as K2,
        KeyDepends as d
    where
        k1.key_id = d.depon and
        k2.key_id = d.depto
    order by
        k1.key_id, k2.key_id
    ;"""


# Add new keyword to table if not exists.  Return keyword ID
def addKeyword(keyWord):
    cur.execute('INSERT OR IGNORE INTO Keywords (keyword) VALUES (?)', (keyWord,))
    cur.execute('SELECT key_id FROM Keywords WHERE keyword = ?', (keyWord,))
    keyWordID = cur.fetchone()[0]
    # print(">>" + keyWord + "<<", keyWordID)
    return keyWordID


# Add new keyword / dependency record
def addDependency(keyWordID, dependencyID):
    # print(keyWordID, dependency_id)
    cur.execute('INSERT OR IGNORE INTO KeyDepends (depon, depto) VALUES (?, ?)', (keyWordID, dependencyID,))
    return


# CSV records; rec[0] = FM Keyword; rec[1] = list of FM Dependencies
with open(csvfile) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        # print(row)
        if line_count > 0:
            keyword_id = addKeyword(row[3])
            dependency_list = row[4].split(';')
            while '' in dependency_list: # Remove unfortunate trailing '' elements
                dependency_list.remove('')
            for dependency in dependency_list:
                dependency_id = addKeyword(dependency)
                addDependency(keyword_id, dependency_id)
        line_count += 1
    print(f'Processed {line_count} lines.')

# Commit and close database
con.commit()





#
cur.execute(sql_query)

#
myFile = open(dotfile, 'w')
myFile.write('digraph FMM {\n')
myFile.write('node [style=filled];\n')

for row in cur:
    myFile.write(f'  \"{row[1]}\" -> \"{row[0]}\" ;\n')

myFile.write("}\n")
myFile.close()











con.close()
