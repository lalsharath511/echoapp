from data_processor import DataProcessor
from text_classifier import TextClassifier
from entityprocessor import EntityProcessor
from settings import CONNECTION_URL, DATABASE_NAME, COLLECTION_POST
from pymongo import MongoClient, errors
import numpy as np

def run_data_processing_workflow():
    """
    Executes the data processing workflow, which includes fetching data from MongoDB, cleaning and processing the data,
    predicting labels, processing entities, calculating engagement scores, and saving the processed data back to MongoDB.
    """
    # Instantiate required classes
    data_processor = DataProcessor()
    text_classifier = TextClassifier()
    entity_processor = EntityProcessor()

    # Fetch new entries from MongoDB
    try:
        new_data = data_processor.fetch_new_entries()
    except Exception as e:
        print(f"Error fetching new entries: {e}")
        return
    
    # Check if new_data is empty
    if new_data is None or new_data.empty:
        print("No new entries found. Exiting workflow.")
        return

    print(f"Number of new entries fetched: {len(new_data)}")

    try:
        # Process the data
        new_data['transform_data_id'] = new_data['_id']
        new_data = new_data.drop('_id', axis=1, errors='ignore')
        new_data['Message'] = new_data['Message'].apply(text_classifier.clean_text)

        # Predict labels for the cleaned data
        df_with_labels = data_processor.predict_labels(new_data)

        # Process entities in the labeled data
        processed_df = entity_processor.process_entities(df=df_with_labels)
        processed_df.replace("", np.nan, inplace=True)

        # Calculate engagement score
        processed_df['engagementScore'] = np.where(
            processed_df['Engagement'].notna() & processed_df['audience'].notna(),
            (processed_df['Engagement'] / processed_df['audience']) * 100,
            0
        )

        # Drop rows with missing 'Message'
        processed_df = processed_df.dropna(subset=['Message'])
        processed_df = data_processor.process_data(processed_df)

        # Connect to MongoDB and insert processed data
        try:
            client = MongoClient(CONNECTION_URL)
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_POST]

            # Convert DataFrame to dictionary and insert into MongoDB
            records = processed_df.to_dict(orient='records')
            
            if records:  # Check if there is data to insert
                collection.insert_many(records)
                print("Data processing workflow completed successfully.")
            else:
                print("No valid data to insert into MongoDB.")
        
        except errors.PyMongoError as db_error:
            print(f"Error inserting data into MongoDB: {db_error}")

    except Exception as e:
        print(f"Unexpected error during processing: {e}")

if __name__ == "__main__":
    run_data_processing_workflow()
