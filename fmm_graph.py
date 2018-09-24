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
import subprocess

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


def find_all_paths(graph, start, path=[], level=0, skip = 0):
    if not start in graph:
        return []
    path = path + [start]
    paths = [path]
    for node in graph[start]:
        level += 1
        if node != skip:
            paths = paths + find_all_paths(graph, node, path, level)
        else:
            print('skipping node:', skip)
            # Add a new keyWord to show items skipped
            skipped_name = keyWords[node] + " skipped..."
            keyWords[999] = skipped_name
            paths = paths + [[start, node],[node, 999]]
    return(paths)


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

# Commit database
con.commit()


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


sql_query4 = \
    """
        select key_id from keywords where key_id not in (select depto from keydepends) order by keyword;
    """

cur.execute(sql_query4)
top_nodes = []
gfz_file_number = 0;

for result in cur.fetchall():
    top_nodes.append(result[0])

pdflist = []
bookmarks = 'bookmark.txt'
bookmarkFile = open(bookmarks, 'w')

for node in top_nodes:
    gfz_file_number += 1
    node_pairs = []

    dotfile = "FMM_" + str(gfz_file_number) + ".gfz"
    pdffile = "FMM_" + str(gfz_file_number) + ".pdf"

    node_name = keyWords[node]
    graph_title = '"' + node_name + '"'

    pathlist = find_all_paths(graph, node, [], 0, 113)

    for path in pathlist:
        for n in range(len(path) - 1):
            node_pair = (path[n], path[n+1])
            if node_pair not in node_pairs:
                node_pairs.append(node_pair)

    # Make graphiz dot file from data
    myFile = open(dotfile, 'w')
    myFile.write('digraph ' + graph_title + ' {\n')
    myFile.write('node [style=filled];\n')
    myFile.write('size = "8,10";\n')
    myFile.write('rankdir = LR;\n')
    myFile.write('labelloc = "t";\n')
    myFile.write(f'label = {graph_title};\n')

    for node_pair in node_pairs:
        depon = keyWords[node_pair[0]]
        depto = keyWords[node_pair[1]]
        myFile.write(f'  \"{depon}\" -> \"{depto}\" ;\n')

    myFile.write("}\n")
    myFile.close()

    # Convert this newly minted gfz file to pdf
    subprocess.run(f'dot -Tpdf {dotfile} -o {pdffile}')
    pdflist.append(pdffile)

    # Make pdf table of contents file dot file from data
    bookmarkFile.write('BookmarkBegin\n')
    bookmarkFile.write(f'BookmarkTitle: {node_name}\n')
    bookmarkFile.write('BookmarkLevel: 1\n')
    bookmarkFile.write(f'BookmarkPageNumber: {gfz_file_number}\n')

bookmarkFile.close()
pdffiles = ' '.join(pdflist)

subprocess.run(f'pdftk {pdffiles} cat output fmm_total.pdf')
subprocess.run(f'pdftk fmm_total.pdf update_info {bookmarks} output fmm_total_final.pdf')

# Close database
con.close()

# error check does not quite work to see if subnodes are subnodes of other nodes
# for node in top_nodes:
#     print("node = ", keyWords[node])
#     for subnode in graph[node]:
#         print("\tsubnode = ", keyWords[subnode])


