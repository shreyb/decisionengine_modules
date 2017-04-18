#!/usr/bin/python

import os
import sqlite3
import traceback

#from UserDict import UserDict
# TODO: Schema definations and validation and updations


class DataSpaceConnectionError(Exception):
    """
    Errors related to database access
    """
    pass


class DataSpaceError(Exception):
    """
    Errors related to database access
    """
    pass


class DataSpace(object):
    """
    DataSpace class provides interface to the database used to store the data
    """

    # Internal variable to inform if the database tables have been created
    _tables_created = False

    #: Description of tables and their columns
    tables = {
        'header': [
            'taskmanager_id TEXT',
            'generation_id INT',
            'key TEXT',
            'create_time REAL',
            'expiration_time REAL',
            'scheduled_create_time REAL',
            'creator TEXT',
            'schema_id INT',
        ],
        'schema': [
            'schema_id INT', # Auto generated
            'schema BLOB',   # keys in the value dict of the dataproduct table
        ],
        'metadata': [
            'taskmanager_id TEXT',
            'generation_id INT',
            'key TEXT',
            'state TEXT',
            'generation_time REAL',
            'missed_update_count INT',
        ],
        'dataproduct': [
            'taskmanager_id TEXT',
            'generation_id INT',
            'key TEXT',
            'value BLOB'
        ]
    }

    #: Name of the dataproduct table
    dataproduct_table = 'dataproduct'

    #: Name of the header table
    header_table = 'header'

    #: Name of the metadata table
    metadata_table = 'metadata'


    def __init__(self, config):
        """
        :type config: :obj:`dict`
        :arg config: Configuration dictionary

        TODO: Change a single connection to the database to a connection pool
        """

        self.db_filename = config['dataspace']['filename']

        if os.path.exists(self.db_filename):
            os.unlink(self.db_filename)

        try:
            # Creates DB if it does not exist
            self.conn = sqlite3.connect(self.db_filename)
        except:
            raise
            #raise DataSpaceConnectionError(
            #    'Error connecting to the database %s' % db_filename)
        if DataSpace._tables_created:
            raise Exception('Tables already created')
        else:
            self.create()


    def close(self):
        """Close all connections to the database"""
        self.conn.close()


    def create(self):
        """
        Create database tables for dataproduct, header and metadata

        TODO: Need to add functionality to ignore if tables exist
        """

        try:
            for table, cols in DataSpace.tables.iteritems():
                if isinstance(cols, list):
                    cmd = """CREATE TABLE %s (%s)""" % (table, ', '.join(str(c) for c in cols))
                    cursor = self.conn.cursor()
                    cursor.execute(cmd)
            self.conn.commit()
            DataSpace._tables_created = True
        except:
             raise
             #traceback.print_stack()
             #raise DataSpaceError('Error creating table %s' % table)


    def get_last_generation_id(self, taskmanager_id):
        """
        Get the last known generation_id for the given taskmanager_id

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        
        :rtype: :obj:`int`

        TODO: COALESCE is not safe. Find a better way check with DB experts
        """

        try:
            cmd = """SELECT COALESCE(MAX(generation_id),0) FROM %s""" % DataSpace.dataproduct_table

            cursor = self.conn.cursor()
            cursor.execute(cmd)
            value = cursor.fetchall()   
	except:
            raise
        return value[0][0]


    def insert(self, taskmanager_id, generation_id, key, value, header, metadata):
        """
        Insert data into respective tables for the given
        taskmanager_id, generation_id, key

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type key: :obj:`string`
        :arg key: key for the value
        :type value: :obj:`object`
        :arg value: Value can be an object or dict
        :type header: :obj:`~datablock.Header`
        :arg header: Header for the value
        :type metadata: :obj:`~datablock.Metadata`
        :arg header: Metadata for the value
        """

        # Insert the data product, header and metadata to the database
        try:
            # Insert value in the dataproduct table
            cmd = """INSERT INTO %s VALUES ("%s", %i, "%s", "%s")""" % (
                DataSpace.dataproduct_table, taskmanager_id, generation_id,
                key, value)
            cursor = self.conn.cursor()
            cursor.execute(cmd)
  
            # Insert header in the header table
            cmd = """INSERT INTO %s VALUES ("%s", %i, "%s", %f, %f, %f, "%s", "%s")""" % (
                DataSpace.header_table, taskmanager_id, generation_id,
                key, header.get('create_time'), header.get('expiration_time'),
                header.get('scheduled_create_time'), header.get('creator'),
                header.get('schema_id'))
            cursor = self.conn.cursor()
            cursor.execute(cmd)

            # Insert metadata in the metadata table
            cmd = """INSERT INTO %s VALUES ("%s", %i, "%s", "%s", %f, %i)""" % (
                DataSpace.metadata_table, taskmanager_id, generation_id,
                key, metadata.get('state'), metadata.get('generation_time'),
                metadata.get('missed_update_count'))
            #print '=========== cmd ==========='
            #print cmd
            #print '=========== cmd ==========='
            cursor = self.conn.cursor()
            cursor.execute(cmd)

            # Commit data/header/metadata as a single transaction
            self.conn.commit()
        except:
            raise
            #traceback.print_stack()
            #raise DataSpaceError('Error creating table %s' % DataSpace.dataproduct_table)


    def update(self, taskmanager_id, generation_id, key, value, header, metadata):
        """
        Update the data in respective tables for the given
        taskmanager_id, generation_id, key

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type key: :obj:`string`
        :arg key: key for the value
        :type value: :obj:`object`
        :arg value: Value can be an object or dict
        :type header: :obj:`~datablock.Header`
        :arg header: Header for the value
        :type metadata: :obj:`~datablock.Metadata`
        :arg header: Metadata for the value
        """

        # Update the data product, header and metadata in the database
        try:
            params = (taskmanager_id, generation_id, key)
            cmd = """UPDATE %s SET value="%s" WHERE ((taskmanager_id=?) AND (generation_id=?) AND (key=?))""" % (DataSpace.dataproduct_table, value)
            cursor = self.conn.cursor()
            cursor.execute(cmd, params)

            cmd = """UPDATE %s SET create_time=%f, expiration_time=%f, scheduled_create_time=%f, creator="%s", schema_id=%i WHERE ((taskmanager_id=?) AND (generation_id=?) AND (key=?))""" % (DataSpace.header_table,
                header.get('create_time'), header.get('expiration_time'),
                header.get('scheduled_create_time'), header.get('creator'),
                header.get('schema_id'))
            cursor = self.conn.cursor()
            cursor.execute(cmd, params)

            cmd = """UPDATE %s SET state="%s", generation_time=%f, missed_update_count=%i WHERE ((taskmanager_id=?) AND (generation_id=?) AND (key=?))""" % (
                DataSpace.metadata_table, metadata.get('state'),
                metadata.get('generation_time'),
                metadata.get('missed_update_count'))
            cursor = self.conn.cursor()
            cursor.execute(cmd, params)

            # Commit data/header/metadata as a single transaction
            self.conn.commit()
        except:
            raise
            #traceback.print_stack()
            #raise DataSpaceError('Error updating table %s' % DataSpace.dataproduct_table)


    def _get_table_row(self, table, taskmanager_id,
                       generation_id, key, cols=None):
        # Get the data product from the database

        if not cols:
            cols = ['*']
        try:
            template = (taskmanager_id, generation_id, key)
            
            #print cmd
            cmd = """SELECT %s FROM %s WHERE ((taskmanager_id=?) AND (generation_id=?) AND (key=?))""" % (', '.join(str(c) for c in cols), table)
            params = (taskmanager_id, generation_id, key)

            cursor = self.conn.cursor()
            cursor.execute(cmd, params)
            value = cursor.fetchall()
        except:
            raise
            #traceback.print_stack()
            #raise DataSpaceError('Error creating table %s' % DataSpace.dataproduct_table)

        return value[-1]
        #return value


    def get_dataproduct(self, taskmanager_id, generation_id, key):
        """
        Return the data from the dataproduct table for the given
        taskmanager_id, generation_id, key

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type key: :obj:`string`
        :arg key: key for the value
        """

        value = self._get_table_row(DataSpace.dataproduct_table, taskmanager_id,
                                    generation_id, key, ['value'])
        return value


    def get_header(self, taskmanager_id, generation_id, key):
        """
        Return the header from the header table for the given
        taskmanager_id, generation_id, key

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type key: :obj:`string`
        :arg key: key for the value
        """

        cols = [(x.split())[0] for x in DataSpace.tables.get(DataSpace.header_table)]
        return self._get_table_row(DataSpace.header_table, taskmanager_id,
                                   generation_id, key, cols)


    def get_metadata(self, taskmanager_id, generation_id, key):
        """
        Return the metadata from the metadata table for the given
        taskmanager_id, generation_id, key

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type key: :obj:`string`
        :arg key: key for the value
        """

        cols = [(x.split())[0] for x in DataSpace.tables.get(DataSpace.metadata_table)]
        return self._get_table_row(DataSpace.metadata_table, taskmanager_id,
                                   generation_id, key, cols)


    def duplicate(self, taskmanager_id, generation_id, new_generation_id):
        """
        For the given taskmanager_id, make a copy of the datablock with given 
        generation_id, set the generation_id for the datablock copy

        :type taskmanager_id: :obj:`string`
        :arg taskmanager_id: taskmanager_id for generation to be retrieved
        :type generation_id: :obj:`int`
        :arg generation_id: generation_id of the data
        :type new_generation_id: :obj:`int`
        :arg new_generation_id: generation_id of the new datablock created
        """

        cursor = self.conn.cursor()
        params = (taskmanager_id, generation_id)

        cmd = """INSERT INTO %s (taskmanager_id, generation_id, key, value) SELECT taskmanager_id, %i, key, value FROM %s WHERE (taskmanager_id=?) AND (generation_id=?)""" % (
            DataSpace.dataproduct_table, new_generation_id,
            DataSpace.dataproduct_table)
        cursor = self.conn.cursor()
        cursor.execute(cmd, params)

        cmd = """INSERT INTO %s (taskmanager_id, generation_id, key, create_time, expiration_time, scheduled_create_time, creator, schema_id) SELECT taskmanager_id, %i, key, create_time, expiration_time, scheduled_create_time, creator, schema_id FROM %s WHERE (taskmanager_id=?) AND (generation_id=?)""" % (
            DataSpace.header_table, new_generation_id,
            DataSpace.header_table)
        cursor = self.conn.cursor()
        cursor.execute(cmd, params)

        cmd = """INSERT INTO %s (taskmanager_id, generation_id, key, state, generation_time, missed_update_count) SELECT taskmanager_id, %i, key, state, generation_time, missed_update_count FROM %s WHERE (taskmanager_id=?) AND (generation_id=?)""" % (
            DataSpace.metadata_table, new_generation_id,
            DataSpace.metadata_table)
        cursor = self.conn.cursor()
        cursor.execute(cmd, params)

        self.conn.commit()


    def delete(self, taskmanager_id, all_generations=False):
        # Remove the latest generation of the datablock
        # If asked, remove all generations of the datablock
        pass
