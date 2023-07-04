import pymongo


def database_count(database_url):
    client = pymongo.MongoClient(database_url)
    db = client.safeeatdb

    for collection in db.list_collection_names():
        result = db.get_collection(collection).count_documents({})
        print(f"INFO: {result} documents in collection {collection}")
