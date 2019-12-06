"""
Manage state of our icloud Media
"""
import os


from icloudpd.paths import local_download_path, local_download_path_lp
from icloudpd.sqlite import SqliteConnector


STATE_ENUM = {0: "FINISHED",
              1: "STARTED",
              2: "NON_EXISTANT",
              "FINISHED": 0,
              "STARTED": 1,
              "NON_EXISTANT": 2}

class FilesMediaManager(object):
    """
    filesystem based media manager
    """
    def __init__(self):
        pass

    def update(self, **kwargs):
        """
        FilesMediaManager has no state to maintain as it is intrinsic when downloaded
        """
        pass

    def processed(self, photo, download_size, download_dir):
        """
        determine if a photo has already been processed
        :param photo: pyicloud_ipd.services.photos.PhotoAsset obj
        :param download_size: size of photo to download.  e.g.: original, small, etc.
                              this determines the file name
        :param download_dir: directory the file should be downloaded to

        """
        # determine download path for a live photos video
        if download_size.endswith("Video"):
            download_path = local_download_path_lp(photo, download_size, download_dir)
        # determine download path for a normal photo
        else:
            download_path = local_download_path(photo, download_size, download_dir)

        file_exists = os.path.isfile(download_path)

        if not file_exists and download_size == "original":
            # Deprecation - We used to download files like IMG_1234-original.jpg,
            # so we need to check for these.
            # Now we match the behavior of iCloud for Windows: IMG_1234.jpg,
            # for original but still IMG_1234-thumb.jpg, IMG_1234-small.jpg, etc.
            original_download_path = ("-%s." % download_size).join(
                download_path.rsplit(".", 1)
            )
            file_exists = os.path.isfile(original_download_path)

        return file_exists


class BaseDBMediaManager(object):
    """
    base database media manager stub
    """
    def __init__(self, filepath):
        self._filepath = filepath
        self._setup()
    def _setup(self):
        raise NotImplementedError("{} is only a stub".format(self.__class__.__name__))
    def processed(self, photo, download_size, **kwargs):
        raise NotImplementedError("{} is only a stub".format(self.__class__.__name__))
    def state(self, photo, download_size):
        raise NotImplementedError("{} is only a stub".format(self.__class__.__name__))
    def update(self, photo, download_size, state):
        raise NotImplementedError("{} is only a stub".format(self.__class__.__name__))


class JsonMediaManager(BaseDBMediaManager):
    """
    Flat file json db based media manager that is unimplemented
    """


class SQLiteMediaManager(BaseDBMediaManager):
    """
    sqlite db based media manager
    """
    TABLE = "photos"
    SCHEMA = ("""CREATE TABLE IF NOT EXISTS `{table}` ("""
             """`id` varchar(28) NOT NULL,"""
             """`size` varchar(30) NOT NULL,"""
             """`state` integer NOT NULL);""")
    # sqlite string substitution character is "?"
    SUB_SYMBOL = """?"""

    def _setup(self):
        self.schema = self.SCHEMA.format(table=self.TABLE)
        self.db = SqliteConnector(db_file=self._filepath, schema=self.schema)

    def processed(self, photo, download_size, **kwargs):
        """
        lookup if our photo is fully processed (e.g.: exists in state store with
        a state of 0 ("FINISHED")
        :param photo: pyicloud_ipd.services.photos.PhotoAsset obj
        :param download_size: size of photo to download.  e.g.: original, small, etc.
        """
        # photo is in finished state
        if self.get_state(photo=photo, download_size=download_size) == 0:
            return True
        else:
            return False

    def update(self, photo, download_size, state):
        """
        update a row in our sqlite state store
        :param photo: pyicloud_ipd.services.photos.PhotoAsset obj
        :param download_size: size of photo to download.  e.g.: original, small, etc.
        :param state: photo download state to update to
        """
        if state not in STATE_ENUM:
            raise Exception("cannot update to unkown state {}".format(state))
        if type(state) == str:
            state = STATE_ENUM[state]

        # remove existing row(s)
        query = "DELETE FROM {0} WHERE id={1} AND size={1}"
        query = query.format(self.TABLE, self.SUB_SYMBOL)
        query_params = (photo.id, download_size)
        self.db.trans_query(query, query_params)

        query = "INSERT INTO {0} (id, size, state) VALUES ({1}, {1}, {1})"
        query = query.format(self.TABLE, self.SUB_SYMBOL)
        query_params = (photo.id, download_size, state)
        self.db.trans_query(query, query_params)

    def get_state(self, photo, download_size):
        query = "SELECT state FROM {0} WHERE id={1} AND size={1}"
        query = query.format(self.TABLE, self.SUB_SYMBOL)
        query_params = (photo.id, download_size)

        rows = self.db.query(query, query_params)
        if len(rows) == 0:
            return STATE_ENUM["NON_EXISTANT"]
        if len(rows) > 1:
            raise Exception("non-unique results {0} querying for photo {0}: size {1}".format(rows, *query_params))
        else:
            return rows[0][0]
