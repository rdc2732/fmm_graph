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
dotfile2 = 'FMM2.gfz'


# Set up sqlite database
# Keyword data will be organized in parent/child relationships.
#  - a keyword may be the child of (dependent on - depon) zero or more other keywords
#  - a keyword may be the parent of (dependency to - depto) zero or more other keywords
#  - depon refers to the dependency in FMM keywork, aka parent role
#  - depto refers to the keyword itself, aka child role
con = sqlite3.connect(sqldbfile)
cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS Keywords")
cur.execute("DROP TABLE IF EXISTS KeyDepends")
cur.execute("CREATE TABLE Keywords (key_id INTEGER PRIMARY KEY, keyword TEXT, UNIQUE (keyword))")
cur.execute("CREATE TABLE KeyDepends (depon INTEGER, depto INTEGER, \
                FOREIGN KEY (depon) REFERENCES Keywords(key_id), \
                FOREIGN KEY (depto) REFERENCES Keywords(key_id))")


# Add new keyword to table if not exists.  Return keyword ID
def addKeyword(keyWord):
    cur.execute('INSERT OR IGNORE INTO Keywords (keyword) VALUES (?)', (keyWord,))
    cur.execute('SELECT key_id FROM Keywords WHERE keyword = ?', (keyWord,))
    keyWordID = cur.fetchone()[0]
    return keyWordID


# Add new keyword / dependency record
def addDependency(parent_id, child_id):
    cur.execute('INSERT OR IGNORE INTO KeyDepends (depon, depto) VALUES (?, ?)', (parent_id, child_id,))
    return


def find_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if not start in graph:
        return None
    for node in graph[start]:
        if node not in path:
            newpath = find_path(graph, node, end, path)
            if newpath:
                return newpath
    return None

def find_all_paths(graph, start, path=[], level=0):
    path = path + [start]
    if not start in graph:
        return []
    paths = []
    print(graph[start])
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, path, level)
            for newpath in newpaths:
                paths.append(newpath)
    return [path]






# CSV records; rec[0] = FM Keyword; rec[1] = list of FM Dependencies
with open(csvfile) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count > 0:
            keyword_id = addKeyword(row[3])
            dependency_list = row[4].split(';')
            while '' in dependency_list: # Remove unfortunate trailing '' elements
                dependency_list.remove('')
            for dependency in dependency_list:
                dependency_id = addKeyword(dependency)
                addDependency(dependency_id, keyword_id)
        line_count += 1
    print(f'Processed {line_count} lines.')

# Commit and close database
con.commit()

##############################################
sql_query = \
    """select
        k1.keyword as Dependency,
        k2.keyword as Dependent
    from
        Keywords as k1,
        Keywords as k2,
        KeyDepends as d
    where
        k1.key_id = d.depon and
        k2.key_id = d.depto
    order by
        k1.key_id, k2.key_id
    ;"""


cur.execute(sql_query)

# Make graphiz dot file from data
myFile = open(dotfile, 'w')
myFile.write('digraph FMM {\n')
myFile.write('node [style=filled];\n')

for row in cur:
    myFile.write(f'  \"{row[0]}\" -> \"{row[1]}\" ;\n')

myFile.write("}\n")
myFile.close()


# ##############################################
# sql_query = \
#     """select
#         k1.keyword as Dependency,
#         k2.keyword as Dependent
#     from
#         Keywords as k1,
#         Keywords as k2,
#         KeyDepends as d
#     where
#         k1.key_id = d.depon and
#         k2.key_id = d.depto
#     order by
#         k1.key_id, k2.key_id
#     ;"""
#
#
# cur.execute(sql_query)
#
# # Make graphiz dot file from data
# myFile = open(dotfile2, 'w')
# myFile.write('digraph FMM2 {\n')
# myFile.write('node [style=filled];\n')
#
# for row in cur:
#     myFile.write(f'  \"{row[1]}\" -> \"{row[0]}\" ;\n')
#
# myFile.write("}\n")
# myFile.close()

# Get list of all top level nodes
# select * from keywords where key_id not in (select depto from keydepends);



# Build directed graph data structure from data.
# The graph will be defined as a dictionary of lists.
#   - the key to each key/value pair will be a node
#   - the value will be a list of directly connected nodes
graph = {}
keyWords = {}

# Get the list of all id's from the keywords table
sql_query2 = \
    """
    select 
        key_id, keyword from keywords
    ;"""


# Make dictionary of key_id and keywords
cur.execute(sql_query2)
for row in cur:
    keyWords[row[0]] = row[1]


# Get this list of dependent ids for a given id
sql_query3 = \
    """
    select
        depto
    from
        keydepends 
    where
        depon = ?
    order by
        depon
    ;"""


# Build out graph based on list of keys
for key in keyWords.keys():
    graph[key] = []
    cur.execute(sql_query3, (key,))
    for result in cur.fetchall():
        graph[key].append(result[0])

# print(graph)


# print("execute find path:", find_path(graph, 2, 402))

print(find_all_paths(graph, 316))

# for key in graph.keys():
#     print(key, keyWords[key], graph[key])


# cur.execute(sql_query2)
# for row in cur:
#     graph[row[0]] = []
#
#
# sql_query4 = \
#     """select
#         t1.keyword as dependency,
#         t2.keyword as dependent
#     from
#         keywords as t1,
#         keywords as t2,
#         keydepends as t3
#     where
#         t1.key_id = t3.depon and
#         t2.key_id = depto
#     order by
#         dependency, dependent
#     ;"""
#
#
#
#

con.close()
