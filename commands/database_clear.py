import pymongo


def database_clear(database_url):
    client = pymongo.MongoClient(database_url)
    db = client.safeeatdb

    for collection in db.list_collection_names():
        result = db.get_collection(collection).delete_many({})
        count = result.deleted_count
        print(f"INFO: Deleted {count} documents from collection {collection}")

    print("INFO: Database cleared")
