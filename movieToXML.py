# CSCI E-66: Problem Set 4, Problem 5
#
#   name:   Johanna Bodnyk
#   email:  bodnyk@gmail.com
#   date:   April 21, 2015

import sqlite3
import xml.etree.ElementTree as ET
import re

class XMLBuilder:

    def __init__(self, table, db):
        
        self.table = table
        self.db = db

        # Set lowercase and plural versions of table name
        # to use as XML elements, and set XML filename
        self.el_name = table.lower()
        if self.table == 'Person':
            self.root_name = 'people'
        else:
            self.root_name = self.el_name + 's'
        self.file_name = self.root_name + '.xml'

        # Define the related records to be added as attributes
        self.related_attributes = []
        if table == 'Person':
            self.related_attributes.append(['Director', 'directed'])
            self.related_attributes.append(['Actor', 'actedIn'])
            self.related_attributes.append(['Oscar', 'oscars'])
        elif table == 'Movie':
            self.related_attributes.append(['Director', 'directors'])
            self.related_attributes.append(['Actor', 'actors'])
            self.related_attributes.append(['Oscar', 'oscars'])


    # Finds related records in a pivot table and sets their ids
    # as an attribute on the current element
    def _set_related(self, pivot, attribute):

        # Set up id field names and id prefix based on tables involved
        person_id_field = pivot.lower() if pivot in ('Actor', 'Director') else 'person'
        person_id_field += '_id'

        if self.table == 'Movie':
            this_id_field = 'movie_id'
            other_id_field = person_id_field
            prefix = 'O' if pivot == 'Oscar' else 'P'
        else:
            this_id_field = person_id_field
            other_id_field = person_id_field if pivot == 'Oscar' else 'movie_id'
            prefix = 'O' if pivot == 'Oscar' else 'M'

        # Query pivot table for related records
        rel_cur = self.db.cursor()
        rel_cur.execute('SELECT * FROM ' + pivot + ' WHERE ' +
                       this_id_field + ' = "' + self.row['id'] + '"')

        # Build string of space-separated prefixed ids of related records
        ids = ''
        for rel_row in rel_cur:
            year = rel_row['year'] if pivot == 'Oscar' else None
            ids += self._make_id(prefix, rel_row[other_id_field], year) + ' '
            
        # Strip trailing space
        ids = ids.strip()
        
        # If related records were found, add ids to element attribute
        if ids:
            self.el.set(attribute, ids)


    # Makes an XML-compliant ID (prefixed with a letter)
    def _make_id(self, prefix, orig_id, year = None):
        if prefix == 'O':   # Oscar id
            new_id = 'O' + str(year)
            new_id += orig_id if orig_id else '0000000'
        else:               # Movie and Person ids
            new_id = prefix + orig_id
        return new_id


    # Build XML file from SQL table(s)
    def buildXML(self):

        # Get cursor for the db
        self.cur = db.cursor() 

        # Get column names (except ID columns)
        self.cur.execute('PRAGMA table_info(' + self.table + ');')
        cols = []
        for col_row in self.cur:
            if not 'id' in col_row[1]:
                cols.append(col_row[1])

        # Get records from primary table
        self.cur.execute('SELECT * FROM ' + self.table)

        # Create root XML element
        root = ET.Element(self.root_name)

        # Create child XML elements for each record
        for self.row in self.cur:

            # Create record element
            self.el = ET.SubElement(root, self.el_name)

            # Set ID attribute(s)
            if self.table in ['Movie', 'Person',]:
                self.el.set('id', self._make_id(self.table[0], self.row['id']))
            else:       # Oscar table - movie_id and person_id are part of Oscar record itself
                self.el.set('id', self._make_id(self.table[0], self.row['person_id'], self.row['year']))
                self.el.set('movie_id', self._make_id('M', self.row['movie_id']))
                if self.row['person_id']:
                    self.el.set('person_id', self._make_id('P', self.row['person_id']))

            # Set attributes for related records
            for rel in self.related_attributes:
                self._set_related(*rel) 

            # Create child elements (fields)
            for col in cols:
                if self.row[col]:   # Omit empty fields
                    field = ET.SubElement(self.el, col)
                    field.text = str(self.row[col])

        # Write XML structure out to file
        tree = ET.ElementTree(root)
        tree.write(self.file_name)
        print(self.file_name + ' has been written.')


    # Format XML file: add <?xml version="1.0"?> to top of file
    # and add line breaks and indenting
    def formatXML(self):
        # Get original file contents
        file = open(self.file_name, 'r')
        contents = file.read()
        file.close()

        # Reopen to write formatted contents
        file = open(self.file_name, 'w')

        # Write prolog to file
        file.write('<?xml version="1.0"?>\n')

        # Add line breaks between tags
        contents = contents.replace('><', '>\n<')

        # Add indenting and write lines back to file
        lines = contents.splitlines(True)
        level = 0   # indent/tab level
        spaces = 4  # spaces per tab
        for line in lines:
            if re.search(r'<(.*)>.*</\1>', line):   # child element (open AND close tags)
                line = ' ' * level * spaces + line      # use current tab level
            elif '</' in line:                      # close tag only
                level -= 1                              # decrement tab level
                line = ' ' * level * spaces + line      # then use new tab level
            else:                                   # open tag only
                line = ' ' * level * spaces + line      # use current tab level
                level += 1                              # then increment tab level
            file.write(line)

        file.close()           

         
        
# Open database file
db_filename = input('Please enter the name of the database file:')
db = sqlite3.connect(db_filename)

# Allow access to fields by column name
db.row_factory = sqlite3.Row 

# Make sure database contains the tables we need
db_tables = []
for row in db.cursor().execute('SELECT name from sqlite_master where type = "table"'):
    db_tables.append(row[0])

tables = ['Movie', 'Oscar', 'Person']

if not set(tables) <= set(db_tables):
    db.close()
    raise Exception('Database file is invalid! Please try again.')

# Process tables into XML
for table in tables:
    x = XMLBuilder(table, db)
    x.buildXML()
    x.formatXML()

db.close()
