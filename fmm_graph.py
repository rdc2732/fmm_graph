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
# cur.execute("DROP TABLE IF EXISTS Keywords")
# cur.execute("DROP TABLE IF EXISTS KeyDepends")
# cur.execute("CREATE TABLE Keywords (key_id INTEGER PRIMARY KEY, keyword TEXT, UNIQUE (keyword))")
# cur.execute("CREATE TABLE KeyDepends (depon INTEGER, depto INTEGER, \
#                 FOREIGN KEY (depon) REFERENCES Keywords(key_id), \
#                 FOREIGN KEY (depto) REFERENCES Keywords(key_id))")


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


print(sql_query)

# Add new keyword to table if not exists.  Return keyword ID
def addKeyword(keyWord):
    cur.execute('INSERT OR IGNORE INTO Keywords (keyword) VALUES (?)', (keyWord,))
    cur.execute('SELECT key_id FROM Keywords WHERE keyword = ?', (keyWord,))
    keyWordID = cur.fetchone()[0]
    print("addKey: \t" + keyWord + '\t' + str(keyWordID))
    return keyWordID


# Add new keyword / dependency record
def addDependency(keyWordID, dependencyID):
    print("\taddDependency: \t" + str(keyWordID) + '\t' + str(dependencyID))
    cur.execute('INSERT OR IGNORE INTO KeyDepends (depon, depto) VALUES (?, ?)', (keyWordID, dependencyID,))
    return


# # CSV records; rec[0] = FM Keyword; rec[1] = list of FM Dependencies
# with open(csvfile) as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',')
#     line_count = 0
#     for row in csv_reader:
#         if line_count > 0:
#             keyword_id = addKeyword(row[3])
#             dependency_list = row[4].split(';')
#             for dependency in dependency_list:
#                 dependency_id = addKeyword(dependency)
#                 addDependency(keyword_id, dependency_id)
#         line_count += 1
#     print(f'Processed {line_count} lines.')

# Commit and close database
con.commit()
con.close()

#
# # 1) Create a dictionary of all signals { sig_id : sig_name}
# sig_dict = {}
# cur.execute('SELECT sig_id, sig_name FROM signals')
# for row in cur:
#     sig_dict[row[0]] = row[1]
#
#
# # 2) Create a dictionary of all modules { mod_id : mod_name}
# mod_dict = {}
# cur.execute('SELECT mod_id, mod_name FROM modules')
# for row in cur:
#     mod_dict[row[0]] = row[1]
#
#
# # 3) For each signal, build the list of output modules { sig_id : [hlr_out] }
# hlrout_dict = {}
# for id in list(sig_dict.keys()):
#     cur.execute(f'SELECT distinct mod_id FROM modsigs WHERE mod_sig_type = "Output" and sig_id = {id}')
#     mods = []
#     for mod in cur.fetchall():
#         mods.append(mod[0])
#     hlrout_dict[id] = mods
#
#
# # 4) For each signal, build the list of input modules { sig_id : [hlr_in] }
# hlrin_dict = {}
# for id in list(sig_dict.keys()):
#     cur.execute(f'SELECT distinct mod_id FROM modsigs WHERE mod_sig_type = "Input" and sig_id = {id}')
#     mods = []
#     for mod in cur.fetchall():
#         mods.append(mod[0])
#     hlrin_dict[id] = mods
#
# con.close()
#
#
# # 5) Collect vectors of from-to hlr modules and their list of signals {(hlrout,hlrin):[sigs]}
# vector_list = {}
# for id in list(sig_dict.keys()):
#     outlist = list(set(hlrout_dict[id]))  # use set to scrub for unique
#     inlist = list(set(hlrin_dict[id]))
#     hlr_pair_list = [(x, y) for x in outlist for y in inlist]
#     for hlr_pair in hlr_pair_list:
#         if hlr_pair in vector_list:
#             sigs = vector_list[hlr_pair]
#             sigs.append(id)
#             vector_list[hlr_pair] = sigs
#         else:
#             vector_list[hlr_pair] = [id]
#
#
# # 7) Write data to .dot file suitable for generating graph with Graphiz
# myFile = open(dotfile, 'w')
# myFile.write('digraph HLR {\n')
# myFile.write('node [style=filled];\n')
# myFile.write('HLR07 [color="lightblue"];\n')
# myFile.write('HLR08 [color="lightblue"];\n')
# myFile.write('HLR09 [color="lightblue"];\n')
# myFile.write('HLR10 [color="yellow"];\n')
#
# for vector in vector_list:
#     hlr_out = mod_dict[vector[0]]
#     hlr_in = mod_dict[vector[1]]
#     count_label = str(len(vector_list[vector]))
#     if (hlr_out == hlr_in):
#         myFile.write(f'  {hlr_out} -> {hlr_in} [label="{count_label}", color="red", fontcolor="red"];\n')
#     else:
#         myFile.write(f'  {hlr_out} -> {hlr_in} [label="{count_label}"];\n')
# myFile.write("}\n")
# myFile.close()
#
#
