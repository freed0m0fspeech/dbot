"""
MongoDataBase plugin to work with MongoDataBase
"""
from pymongo import MongoClient, errors, ReturnDocument
from pymongo.server_api import ServerApi
from pymongo.cursor import Cursor
from urllib.parse import quote_plus
from typing import Optional


class MongoDataBase:
    """
    **Class to work with MongoDatabase**
    """

    def __init__(self, host, user, passwd):
        self.__host = host
        self.__user = user
        self.__passwd = passwd
        self.client = None
        self.get_connection()

    def get_connection(self) -> bool:
        """
        **Get connection to MongoDataBase**

        :param host: Host link to MongoDataBase
        :param user: Username of MongoDataBase client
        :param passwd: Password of MongoDataBase client
        :return: bool
        """
        host = self.__host
        user = self.__user
        passwd = self.__passwd
        uri = "mongodb+srv://%s:%s@%s" % (quote_plus(user), quote_plus(passwd), host)

        # mdb_client = pymongo.MongoClient(
        #    f"mongodb+srv://{user}:{passwd}@botcluster.iy7wi.mongodb.net/AiogramBot?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE")
        try:
            mdb_client = MongoClient(uri, server_api=ServerApi('1'))

            # The ping command is cheap and does not require auth.
            mdb_client.admin.command('ping')
            # print("You successfully connected to MongoDB!")
            self.client = mdb_client
            return True
        except Exception as e:
            print(e)
            # print(e)
            self.client = None
            return False
            # return None
        # except errors.ConnectionFailure:
        #     print("MongoDataBase server not available")
        #     return None
        # except errors.OperationFailure:
        #     print("MongoDataBasee authentication failed")
        #     return None

        # return mdb_client

    def check_connection(self):
        if not self.client:
            if not self.client.get_connection():
                return False
        else:
            try:
                self.client.admin.command('ping')
            except Exception as e:
                return False

        return True

    def update_field(self, database_name: str, collection_name: str, action: str, query: dict,
                     filter: Optional[dict] = {},
                     return_document: Optional[ReturnDocument] = ReturnDocument.AFTER,
                     upsert: Optional[bool] = True, updateMany=False) -> Optional[dict]:
        """
        **Update document field in MongoDataBase**\n
        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param action: Action that applies to field
        :param query: query to replace in collection (example {'guilds.guildID': '228'})
        :param filter: Optional filter
        :param return_document: Optional[ReturnDocument] determine return document
        :param upsert: Optional upsert value to upsert document if it does not exist
        :return: typing.Optional[dict]

        ----

        - Fields

        ----

        `$currentDate` Sets the value of a field to current date, either as a Date or a Timestamp.\n
        `$inc` Increments the value of the field by the specified amount.\n
        `$min` Only updates the field if the specified value is less than the existing field value.\n
        `$max` Only updates the field if the specified value is greater than the existing field value.\n
        `$mul` Multiplies the value of the field by the specified amount.\n
        `$rename` Renames a field.\n
        `$set` Sets the value of a field in a document.\n
        `$setOnInsert` Sets the value of a field if an update results in an insert of a document. Has no effect on update operations that modify existing documents.\n
        `$unset` Removes the specified field from a document.\n

        ----

        - Array

        ----

        `$` Acts as a placeholder to update the first element that matches the query condition.\n
        `$[]` Acts as a placeholder to update all elements in an array for the documents that match the query condition.\n
        `$[<identifier>]` Acts as a placeholder to update all elements that match the arrayFilters condition for the
        documents that match the query condition.\n
        `$addToSet` Adds elements to an array only if they do not already exist in the set.\n
        `$pop` Removes the first or last item of an array.\n
        `$pull` Removes all array elements that match a specified query.\n
        `$push` Adds an item to an array.\n
        `$pullAll` Removes all matching values from an array.\n

        ----

        - Modifiers

        ----

        `$each` Modifies the $push and $addToSet operators to append multiple items for array updates.\n
        `$position` Modifies the $push operator to specify the position in the array to add elements.\n
        `$slice` Modifies the $push operator to limit the size of updated arrays.\n
        `$sort` Modifies the $push operator to reorder documents stored in an array.\n

        ----

        - Bitwise

        ----

        `$bit` Performs bitwise AND, OR, and XOR updates of integer values.
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            update = {action: query}

            if updateMany:
                collection.update_many(filter=filter, update=update, upsert=upsert)
                return {}

            return collection.find_one_and_update(filter=filter, update=update, return_document=return_document,
                                                  upsert=upsert)

        except Exception as e:
            return None

    def delete_field(self, database_name: str, collection_name: str, query: dict,
                     filter: Optional[dict] = {},
                     return_document: Optional[ReturnDocument] = ReturnDocument.AFTER) -> \
            Optional[dict]:
        """
        **Delete document field from MongoDataBase**

        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param query: {key: 1} to delete in collection
        :param filter: Optional filter
        :param return_document: Optional[ReturnDocument] determine return document
        :param upsert: Optonal upsert value to upsert document if it does not exist
        :return: typing.Optaional[dict]
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            update = {'$unset': query}

            return collection.find_one_and_update(filter=filter, update=update, return_document=return_document)
        except Exception as e:
            return None

    def get_document(self, database_name: str, collection_name: str, filter: Optional[dict] = {},
                     query: Optional[dict] = None) -> Optional[dict]:
        """
        **Get first document from collection in MongoDataBase**

        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param collection_field: Field name
        :param filter: Optional filter
        :param query: Query
        :return: typing.Optional[dict]
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            dict = collection.find_one(filter, query)

            if not dict:
                return {}

        except Exception as e:
            return {}

        return dict

    def get_documents(self, database_name: str, collection_name: str, filter: Optional[dict] = {},
                      query: Optional[dict] = None) -> Optional[Cursor]:
        """
        **Get documents from collection in MongoDataBase**

        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param filter: Optional filter
        :param query: Query
        :return: typing.Optional[pymongo.cursor.Cursor]
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            cursor = collection.find(filter, query)
        except Exception as e:
            return None

        return cursor

    def update_document(self, database_name: str, collection_name: str, document: dict,
                        filter: Optional[dict] = {},
                        return_document: Optional[ReturnDocument] = ReturnDocument.AFTER,
                        upsert: Optional[bool] = True) -> Optional[dict]:
        """
        **Replace document from collection in MongoDataBase**

        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param document: Document to replace
        :param filter: Optional filter
        :param return_document: Optional[ReturnDocument] determine return document
        :param upsert: Optonal upsert value to upsert document if it does not exist
        :return: typing.Optaional[dict]
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            return collection.find_one_and_replace(filter=filter, replacement=document, return_document=return_document,
                                                   upsert=upsert)
        except Exception as e:
            return None

    def delete_document(self, database_name: str, collection_name: str,
                        filter: Optional[dict] = {}) -> Optional[dict]:
        """
        **Delete document from collection in MongoDataBase**

        :param database_name: MongoDataBase name
        :param collection_name: Collection name
        :param filter: Optional filter
        :return: typing.Optaional[dict]
        """

        try:
            database = self.client.get_database(database_name)
            collection = database.get_collection(collection_name)

            return collection.find_one_and_delete(filter=filter)
        except Exception as e:
            return None
