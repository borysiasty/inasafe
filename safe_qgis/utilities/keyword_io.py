"""**Keyword IO implementation.**

.. tip:: Provides functionality for reading and writing keywords from within
   QGIS. It is an abstration for the keywords system used by the underlying
   library.

"""

__author__ = 'tim@linfiniti.com'
__revision__ = '$Format:%H$'
__date__ = '29/01/2011'
__license__ = "GPL"
__copyright__ = 'Copyright 2012, Australia Indonesia Facility for '
__copyright__ += 'Disaster Reduction'

import os
import logging
import sqlite3 as sqlite
from sqlite3 import OperationalError
import cPickle as pickle

from PyQt4.QtCore import QObject
from PyQt4.QtCore import QSettings
from qgis.core import QgsMapLayer

from safe_qgis.exceptions import (
    HashNotFoundError,
    KeywordNotFoundError,
    KeywordDbError,
    InvalidParameterError)
from safe_qgis.safe_interface import (
    verify,
    readKeywordsFromFile,
    writeKeywordsToFile)
from safe_qgis.utilities.utilities import qgis_version

LOGGER = logging.getLogger('InaSAFE')


class KeywordIO(QObject):
    """Class for doing keyword read/write operations.

    It abstracts away differences between using SAFE to get keywords from a
    .keywords file and this plugins implemenation of keyword caching in a local
    sqlite db used for supporting keywords for remote datasources."""

    def __init__(self):
        """Constructor for the KeywordIO object.

        Args:
            None
        Returns:
            None
        Raises:
            None
        """
        QObject.__init__(self)
        # path to sqlite db path
        self.keywordDbPath = None
        self.setup_keyword_db_path()
        self.connection = None

    def set_keyword_db_path(self, path):
        """Set the path for the keyword database (sqlite).

        The file will be used to search for keywords for non local datasets.

        :param path: A valid path to a sqlite database. The database does
            not need to exist already, but the user should be able to write
            to the path provided.
        :type path: str
        """
        self.keywordDbPath = str(path)

    def read_keywords(self, layer, keyword=None):
        """Read keywords for a datasource and return them as a dictionary.

        This is a wrapper method that will 'do the right thing' to fetch
        keywords for the given datasource. In particular, if the datasource
        is remote (e.g. a database connection) it will fetch the keywords from
        the keywords store.

        :param layer:  A QGIS QgsMapLayer instance that you want to obtain
            the keywords for.
        :type layer: QgsMapLayer

        :param keyword: If set, will extract only the specified keyword
              from the keywords dict.
        :type keyword: str

        :returns: A dict if keyword is omitted, otherwise the value for the
            given key if it is present.
        :rtype: dict, str
        """
        mySource = str(layer.source())
        myFlag = self.are_keywords_file_based(layer)

        try:
            if myFlag:
                myKeywords = readKeywordsFromFile(mySource, keyword)
            else:
                myKeywords = self.readKeywordFromUri(mySource, keyword)
            return myKeywords
        except (HashNotFoundError, Exception, OperationalError):
            raise

    def write_keywords(self, layer, keywords):
        """Write keywords for a datasource.
        This is a wrapper method that will 'do the right thing' to store
        keywords for the given datasource. In particular, if the datasource
        is remote (e.g. a database connection) it will write the keywords from
        the keywords store.

        :param layer: A QGIS QgsMapLayer instance.
        :type layer: QgsMapLayer

        :param keywords: A dict containing all the keywords to be written
              for the layer.
        :type keywords: dict
        """
        mySource = str(layer.source())
        myFlag = self.are_keywords_file_based(layer)
        try:
            if myFlag:
                writeKeywordsToFile(mySource, keywords)
            else:
                self.write_keywords_for_uri(mySource, keywords)
            return
        except:
            raise

    def update_keywords(self, layer, keywords):
        """Write keywords for a datasource.


        :param layer: A QGIS QgsMapLayer instance.
        :type layer: QgsMapLayer

        :param keywords: A dict containing all the keywords to be updated
              for the layer.
        :type keywords: dict
        """
        try:
            myKeywords = self.read_keywords(layer)
        except (HashNotFoundError, OperationalError, InvalidParameterError):
            myKeywords = {}
        myKeywords.update(keywords)
        try:
            self.write_keywords(layer, myKeywords)
        except OperationalError, e:
            myMessage = self.tr('Keyword database path: ') + self\
                .keywordDbPath
            raise KeywordDbError(str(e) + '\n' + myMessage)

    def copy_keywords(
            self,
            source_layer,
            destination_file,
            extra_keywords=None):
        """Helper to copy the keywords file from a source to a target dataset.

        e.g.::

            copyKeywords('foo.shp', 'bar.shp')

        Will result in the foo.keywords file being copied to bar.keyword.

        Optional argument extraKeywords is a dictionary with additional
        keywords that will be added to the destination file
        e.g::

            copyKeywords('foo.shp', 'bar.shp', {'resolution': 0.01})

        :param source_layer: A QGIS QgsMapLayer instance.
        :type source_layer: QgsMapLayer

        :param destination_file: The output filename that should be used
              to store the keywords in. It can be a .shp or a .keywords for
              example since the suffix will always be replaced with .keywords.
        :type destination_file: str

        :param extra_keywords: A dict containing all the extra keywords
            to be written for the layer. The written keywords will consist of
            any original keywords from the source layer's keywords file and
            and the extra keywords (which will replace the source layers
            keywords if the key is identical).
        :type extra_keywords: dict

        """
        myKeywords = self.read_keywords(source_layer)
        if extra_keywords is None:
            extra_keywords = {}
        myMessage = self.tr('Expected extraKeywords to be a dictionary. Got '
                            '%s' % str(type(extra_keywords))[1:-1])
        verify(isinstance(extra_keywords, dict), myMessage)
        # compute the output keywords file name
        myDestinationBase = os.path.splitext(destination_file)[0]
        myNewDestination = myDestinationBase + '.keywords'
        # write the extra keywords into the source dict
        try:
            for key in extra_keywords:
                myKeywords[key] = extra_keywords[key]
            writeKeywordsToFile(myNewDestination, myKeywords)
        except Exception, e:
            myMessage = self.tr(
                'Failed to copy keywords file from : \n%s\nto\n%s: %s' % (
                source_layer.source(), myNewDestination, str(e)))
            raise Exception(myMessage)
        return

    def clear_keywords(self, layer):
        """Convenience method to clear a layer's keywords.

        :param layer: A QGIS QgsMapLayer instance.
        :type layer: QgsMapLayer
        """

        self.write_keywords(layer, dict())

    def delete_keywords(self, layer, keyword):
        """Delete the keyword for a given layer..

        This is a wrapper method that will 'do the right thing' to fetch
        keywords for the given datasource. In particular, if the datasource
        is remote (e.g. a database connection) it will fetch the keywords from
        the keywords store.

        :param layer: - A QGIS QgsMapLayer instance.
        :type layer: QgsMapLayer

        :param keyword: The specified keyword will be deleted
              from the keywords dict.
        :type keyword: str

        :returns: True if the keyword was sucessfully delete. False otherwise
        :rtype: bool
        """

        try:
            myKeywords = self.read_keywords(layer)
            myKeywords.pop(keyword)
            self.write_keywords(layer, myKeywords)
            return True
        except (HashNotFoundError, KeyError):
            return False

# methods below here should be considered private

    def default_keyword_db_path(self):
        """Helper to get the default path for the keywords file.

        :returns: The path to where the default location of the keywords
            database is. Maps to which is <plugin dir>/keywords.db
        :rtype: str
        """
        myParentDir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../'))
        return os.path.join(myParentDir, '../../keywords.db')

    def setup_keyword_db_path(self):
        """Helper to set the active path for the keywords.

        Called at init time, you can override this path by calling
        set_keyword_db_path.setKeywordDbPath.

        :returns: The path to where the keywords file is. If the user has
            never specified what this path is, the defaultKeywordDbPath is
            returned.
        :rtype: str
        """
        mySettings = QSettings()
        myPath = mySettings.value(
            'inasafe/keywordCachePath',
            self.default_keyword_db_path()).toString()
        self.keywordDbPath = str(myPath)

    def open_connection(self):
        """Open an sqlite connection to the keywords database.

        By default the keywords database will be used in the plugin dir,
        unless an explicit path has been set using setKeywordDbPath, or
        overridden in QSettings. If the db does not exist it will
        be created.

        :raises: An sqlite.Error is raised if anything goes wrong
        """
        self.connection = None
        try:
            self.connection = sqlite.connect(self.keywordDbPath)
        except (OperationalError, sqlite.Error):
            LOGGER.exception('Failed to open keywords cache database.')
            raise

    def close_connection(self):
        """Close the active sqlite3 connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_cursor(self):
        """Get a cursor for the active connection.

        The cursor can be used to execute arbitrary queries against the
        database. This method also checks that the keywords table exists in
        the schema, and if not, it creates it.

        :returns: A valid cursor opened against the connection.
        :rtype: sqlite.

        :raises: An sqlite.Error will be raised if anything goes wrong.
        """
        if self.connection is None:
            try:
                self.open_connection()
            except OperationalError:
                raise
        try:
            myCursor = self.connection.cursor()
            myCursor.execute('SELECT SQLITE_VERSION()')
            myData = myCursor.fetchone()
            LOGGER.debug("SQLite version: %s" % myData)
            # Check if we have some tables, if not create them
            mySQL = 'select sql from sqlite_master where type = \'table\';'
            myCursor.execute(mySQL)
            myData = myCursor.fetchone()
            LOGGER.debug("Tables: %s" % myData)
            if myData is None:
                LOGGER.debug('No tables found')
                mySQL = ('create table keyword (hash varchar(32) primary key,'
                         'dict text);')
                LOGGER.debug(mySQL)
                myCursor.execute(mySQL)
                #myData = myCursor.fetchone()
                myCursor.fetchone()
            else:
                LOGGER.debug('Keywords table already exists')

            return myCursor
        except sqlite.Error, e:
            LOGGER.debug("Error %s:" % e.args[0])
            raise

    def are_keywords_file_based(self, layer):
        """Check if keywords should be read/written to file or our keywords db.


        :param layer: The layer which want to know how the keywords are stored.
        :type layer: QgsMapLayer

        :returns: True if keywords are stored in a file next to the dataset,
            else False if the dataset is remove e.g. a database.
        :rtype: bool
        """
        # determine which keyword lookup system to use (file base or cache db)
        # based on the layer's provider type. True indicates we should use the
        # datasource as a file and look for a keywords file, false and we look
        # in the keywords db.
        myProviderType = None
        myVersion = qgis_version()
        # check for old raster api with qgis < 1.8
        # ..todo:: Add test for plugin layers too
        if (myVersion < 10800 and
                layer.type() == QgsMapLayer.RasterLayer):
            myProviderType = str(layer.providerKey())
        else:
            myProviderType = str(layer.providerType())

        myProviderDict = {'ogr': True,
                          'gdal': True,
                          'gpx': False,
                          'wms': False,
                          'spatialite': False,
                          'delimitedtext': True,
                          'postgres': False}
        myFileBasedKeywords = False
        if myProviderType in myProviderDict:
            myFileBasedKeywords = myProviderDict[myProviderType]
        return myFileBasedKeywords

    def hash_for_datasource(self, data_source):
        """Given a data_source, return its hash.

        :param data_source: The data_source name from a layer.
        :type data_source: str

        :returns: An md5 hash for the data source name.
        :rtype: str
        """
        import hashlib
        myHash = hashlib.md5()
        myHash.update(data_source)
        myHash = myHash.hexdigest()
        return myHash

    def delete_keywords_for_uri(self, uri):
        """Delete keywords for a URI in the keywords database.

        A hash will be constructed from the supplied uri and a lookup made
        in a local SQLITE database for the keywords. If there is an existing
        record for the hash, the entire record will be erased.

        .. seealso:: write_keywords_for_uri, read_keywords_for_uri

        :param uri: A layer uri. e.g.
            'dbname=\'osm\' host=localhost port=5432 user=\'foo\'
             password=\'bar\' sslmode=disable key=\'id\' srid=4326
        :type uri: str
        """
        myHash = self.hash_for_datasource(uri)
        try:
            myCursor = self.get_cursor()
            #now see if we have any data for our hash
            mySQL = 'delete from keyword where hash = \'' + myHash + '\';'
            myCursor.execute(mySQL)
            self.connection.commit()
        except sqlite.Error, e:
            LOGGER.debug("SQLITE Error %s:" % e.args[0])
            self.connection.rollback()
        except Exception, e:
            LOGGER.debug("Error %s:" % e.args[0])
            self.connection.rollback()
            raise
        finally:
            self.close_connection()

    def write_keywords_for_uri(self, uri, keywords):
        """Write keywords for a URI into the keywords database. All the
        keywords for the uri should be written in a single operation.
        A hash will be constructed from the supplied uri and a lookup made
        in a local SQLITE database for the keywords. If there is an existing
        record it will be updated, if not, a new one will be created.

        .. seealso:: read_keyword_from_uri, delete_keywords_for_uri

        :param uri: A layer uri. e.g.
            'dbname=\'osm\' host=localhost port=5432 user=\'foo\'
             password=\'bar\' sslmode=disable key=\'id\' srid=4326
        :type uri: str

        :param keywords: The metadata keywords to write (which should be
            provided as a dict of key value pairs).
        :type keywords: dict

        :returns: The retrieved value for the keyword if the keyword argument
            is specified, otherwise the complete keywords dictionary is
            returned.

        :raises: KeywordNotFoundError if the keyword is not recognised.
        """
        myHash = self.hash_for_datasource(uri)
        try:
            myCursor = self.get_cursor()
            #now see if we have any data for our hash
            mySQL = 'select dict from keyword where hash = \'' + myHash + '\';'
            myCursor.execute(mySQL)
            myData = myCursor.fetchone()
            myPickle = pickle.dumps(keywords, pickle.HIGHEST_PROTOCOL)
            if myData is None:
                #insert a new rec
                #myCursor.execute('insert into keyword(hash) values(:hash);',
                #             {'hash': myHash})
                myCursor.execute(
                    'insert into keyword(hash, dict) values(:hash, :dict);',
                    {'hash': myHash, 'dict': sqlite.Binary(myPickle)})
                self.connection.commit()
            else:
                #update existing rec
                myCursor.execute(
                    'update keyword set dict=? where hash = ?;',
                    (sqlite.Binary(myPickle), myHash))
                self.connection.commit()
        except sqlite.Error:
            LOGGER.exception('Error writing keywords to SQLite db %s' %
                             self.keywordDbPath)
            # See if we can roll back.
            if self.connection is not None:
                self.connection.rollback()
            raise
        finally:
            self.close_connection()

    def readKeywordFromUri(self, uri, keyword=None):
        """Get metadata from the keywords file associated with a URI.

        This is used for layers that are non local layer (e.g. postgresql
        connection) and so we need to retrieve the keywords from the sqlite
        keywords db.

        A hash will be constructed from the supplied uri and a lookup made
        in a local SQLITE database for the keywords. If there is an existing
        record it will be returned, if not and error will be thrown.

        .. seealso:: write_keywords_for_uri, delete_keywords_for_uri

        :param uri: A layer uri. e.g.
            'dbname=\'osm\' host=localhost port=5432 user=\'foo\'
             password=\'bar\' sslmode=disable key=\'id\' srid=4326
        :type uri: str

        :param keyword: The metadata keyword to retrieve. If none,
            all keywords are returned.
        :type keyword: dict

        Returns:
           A string containing the retrieved value for the keyword if
           the keyword argument is specified, otherwise the
           complete keywords dictionary is returned.

        Raises:
           KeywordNotFoundError if the keyword is not found.
        """
        myHash = self.hash_for_datasource(uri)
        try:
            self.open_connection()
        except OperationalError:
            raise
        try:
            myCursor = self.get_cursor()
            #now see if we have any data for our hash
            mySQL = 'select dict from keyword where hash = \'' + myHash + '\';'
            myCursor.execute(mySQL)
            myData = myCursor.fetchone()
            #unpickle it to get our dict back
            if myData is None:
                raise HashNotFoundError('No hash found for %s' % myHash)
            myData = myData[0]  # first field
            myDict = pickle.loads(str(myData))
            if keyword is None:
                return myDict
            if keyword in myDict:
                return myDict[keyword]
            else:
                raise KeywordNotFoundError('Keyword "%s" not found in %s' % (
                    keyword, myDict))

        except sqlite.Error, e:
            LOGGER.debug("Error %s:" % e.args[0])
        except Exception, e:
            LOGGER.debug("Error %s:" % e.args[0])
            raise
        finally:
            self.close_connection()

    def get_statistics(self, layer):
        """Get the statistics related keywords from a layer.

        :param layer: A QGIS layer that represents an impact.
        :type layer: QgsMapLayer

        :returns: A two-tuple containing the values for the keywords
            'statistics_type' and 'statistics_classes'.
        :rtype: tuple(str, str)

        """
        #find needed statistics type
        try:
            myStatisticsType = self.read_keywords(
                layer, 'statistics_type')
            myStatisticsClasses = self.read_keywords(
                layer, 'statistics_classes')

        except KeywordNotFoundError:
            #default to summing
            myStatisticsType = 'sum'
            myStatisticsClasses = {}

        return myStatisticsType, myStatisticsClasses
