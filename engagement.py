from settings import CONNECTION_URL,DATABASE_NAME,COLLECTION_UPLOAD
from pymongo import MongoClient, ASCENDING

def categorize_and_store_engagement_buckets():
    """
    Categorizes engagement values from the 'uploaded_data' collection into predefined buckets
    and stores the results in the 'engagement_buckets' collection. Each entry in the output
    collection includes the bucket category, the original document ID, and the document itself.
    A unique index is enforced on the 'document_id' field to prevent duplicates.

    Steps:
    1. Connects to the MongoDB database.
    2. Creates a unique index on the 'document_id' field in the output collection.
    3. Iterates through all documents in the input collection.
    4. Categorizes engagement values into buckets: '0-100', '101-500', '501-1000', or '1000+'.
    5. Stores the categorized data in the output collection.
    6. Closes the database connection.
    """
    # Connect to the MongoDB database
    client = MongoClient(CONNECTION_URL)
    db = client[DATABASE_NAME]

    # Define input and output collections
    input_collection = db[COLLECTION_UPLOAD]
    output_collection = db['engagement_buckets']

    # Ensure a unique index on 'document_id' to prevent duplicate entries
    output_collection.create_index([('document_id', ASCENDING)], unique=True)

    # Fetch all documents from the input collection
    all_documents = input_collection.find()

    # Categorize engagement values and store results in the output collection
    for document in all_documents:
        if 'engagement' in document:
            engagement_value = document['engagement']
            document_id = document['_id']

            # Determine the engagement bucket
            if 0 <= engagement_value <= 100:
                bucket = '0-100'
            elif 101 <= engagement_value <= 500:
                bucket = '101-500'
            elif 501 <= engagement_value <= 1000:
                bucket = '501-1000'
            elif engagement_value > 1000:
                bucket = '1000+'
            else:
                bucket = None

            # Insert the categorized data into the output collection
            if bucket:
                output_collection.insert_one({
                    'bucket': bucket,
                    'document_id': document_id,
                    'document': document
                })

    # Close the database connection
    client.close()

# Example usage
if __name__ == "__main__":
    categorize_and_store_engagement_buckets()