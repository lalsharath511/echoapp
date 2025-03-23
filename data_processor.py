from settings import CONNECTION_URL,DATABASE_NAME,COLLECTION_KEYWORD,COLLECTION_UPLOAD,COLLECTION_POST
from pymongo import MongoClient
import pandas as pd
import pickle
import numpy as np

class DataProcessor:
    def __init__(self):
        """
        Initializes the DataProcessor class by setting up the MongoDB connection and fetching keyword data.
        """
        self.client = MongoClient(CONNECTION_URL)
        self.db = self.client[DATABASE_NAME]
        self.keywords = self.fetch_data_from_mongo(COLLECTION_KEYWORD)

    def fetch_data_from_mongo(self, collection_name):
        """
        Fetches data from a specified MongoDB collection and returns it as a pandas DataFrame.

        Args:
            collection_name (str): The name of the MongoDB collection to fetch data from.

        Returns:
            pd.DataFrame: A DataFrame containing the fetched data, or None if an error occurs.
        """
        try:
            collection = self.db[collection_name]
            cursor = collection.find()
            return pd.DataFrame(list(cursor))
        except Exception as e:
            print(f"Error fetching data from MongoDB: {e}")
            return None

    def fetch_new_entries(self):
        """
        Fetches new entries from the 'uploaded_data' collection that are not present in the 'posts' collection.

        Returns:
            pd.DataFrame: A DataFrame containing the new entries.
        """
        uploaded_data_collection = self.db[COLLECTION_UPLOAD]
        posts_collection = self.db[COLLECTION_POST]
        existing_ids = set(post["transform_data_id"] for post in posts_collection.find({}, {"transform_data_id": 1}))
        new_entries = list(uploaded_data_collection.find({"_id": {"$nin": list(existing_ids)}}))
        return pd.DataFrame(list(new_entries))

    def update_engagement_bucket(self, df):
        """
        Cleans the 'engagement_bucket' column by removing the word 'Engagement' and stripping any extra spaces.

        Args:
            df (pd.DataFrame): The DataFrame containing the 'engagement_bucket' column.

        Returns:
            pd.DataFrame: The DataFrame with the updated 'engagement_bucket' column.
        """
        if "engagement_bucket" in df.columns:
            df["engagement_bucket"] = df["engagement_bucket"].str.replace("Engagement", "", regex=True).str.strip()
        return df

    def assign_random_video_values(self, df):
        """
        Assigns random video views, duration, and duration bucket values for rows where the post type is 'Video'.

        Args:
            df (pd.DataFrame): The DataFrame containing video-related data.

        Returns:
            pd.DataFrame: The DataFrame with updated video-related columns.
        """
        if "Video Duration Bucket" not in df.columns:
            df["Video Duration Bucket"] = ""
        df["Video Duration"] = df["Video Duration"].astype(str)
        df["Video Duration Bucket"] = df["Video Duration Bucket"].astype(str)

        for idx, row in df.iterrows():
            if row.get("Post Type") == "Video":
                df.at[idx, "Video Views"] = np.random.randint(100, 10001)
                video_duration_sec = np.random.randint(30, 901)
                df.at[idx, "Video Duration"] = f"{video_duration_sec // 60}:{video_duration_sec % 60:02d}"
                df.at[idx, "Video Duration Bucket"] = self.assign_duration_bucket(video_duration_sec)
        return df

    def assign_duration_bucket(self, duration_sec):
        """
        Assigns a duration bucket based on the video duration in seconds.

        Args:
            duration_sec (int): The duration of the video in seconds.

        Returns:
            str: The corresponding duration bucket.
        """
        if duration_sec <= 30:
            return "5-30 Sec"
        elif 31 <= duration_sec <= 59:
            return "31-59 Sec"
        elif 60 <= duration_sec <= 119:
            return "1-2 Min"
        elif 120 <= duration_sec <= 299:
            return "2-5 Min"
        elif 300 <= duration_sec <= 599:
            return "5-10 Min"
        else:
            return ">10 Min"

    def process_data(self, df):
        """
        Processes the DataFrame by updating the engagement bucket and assigning random video values.

        Args:
            df (pd.DataFrame): The DataFrame to be processed.

        Returns:
            pd.DataFrame: The processed DataFrame.
        """
        df = self.update_engagement_bucket(df)
        df = self.assign_random_video_values(df)
        return df

    def update_themes_subthemes(self, text, keyword_data):
        """
        Updates themes and subthemes based on keyword matching in the provided text.

        Args:
            text (str): The text to search for keywords.
            keyword_data (pd.DataFrame): The DataFrame containing keywords, themes, and subthemes.

        Returns:
            tuple: A tuple containing the matched theme, subtheme, and subsubtheme (if any).
        """
        for keyword, theme, subtheme in zip(keyword_data['Keyword'], keyword_data['Theme'], keyword_data['Sub Theme']):
            keyword = keyword.lower().replace('#', '')
            if keyword in text.lower():
                return theme, subtheme, None
        return None, None, None

    def predict_labels(self, new_data):
        """
        Predicts labels (themes, subthemes, and subsubthemes) for the new data using a pre-trained model.

        Args:
            new_data (pd.DataFrame): The DataFrame containing the new data to be labeled.

        Returns:
            pd.DataFrame: The DataFrame with predicted labels and derived timestamp fields.
        """
        with open("model_q2.pkl", 'rb') as model_file:
            model_bytes = model_file.read()
        model = pickle.loads(model_bytes)
        tfidf_vectorizer = model['tfidf_vectorizer']
        gb_classifier = model['gb_classifier']
        new_data = new_data.apply(self.apply_keyword_matching, axis=1)
        new_data_tfidf = tfidf_vectorizer.transform(new_data['Message'])
        predicted_labels = gb_classifier.predict(new_data_tfidf)

        df = pd.DataFrame([x.strip().split('||') for x in predicted_labels], columns=['Themes', 'Subthemes', 'Subsubthemes'])
        new_data[['Themes', 'Subthemes', 'Subsubthemes']] = df[['Themes', 'Subthemes', 'Subsubthemes']]
        new_data.reset_index(drop=True, inplace=True)
        df = new_data
        df = self.categorize_duplicates(df)
        df['Timestamp'] = df['Publish Date / Time'].apply(self.derive_date_fields)
        df['Publish Date / Time'] = pd.to_datetime(df['Publish Date / Time'], format='%d-%m-%Y %H:%M:%S')
        return df

    def derive_date_fields(self, timestamp_str):
        """
        Derives various date and time fields from a timestamp string.

        Args:
            timestamp_str (str): The timestamp string to be processed.

        Returns:
            dict: A dictionary containing various derived date and time fields.
        """
        timestamp = pd.to_datetime(timestamp_str, dayfirst=True)
        formatted_date = timestamp.strftime('%d-%m-%Y')
        formatted_time = timestamp.strftime('%H:%M:%S')
        day_of_month = timestamp.day
        month = timestamp.month
        year = timestamp.year
        day_of_week = timestamp.strftime('%a')
        week_number = timestamp.strftime('%U')
        date_type = 'Weekend' if timestamp.weekday() in [5, 6] else 'Weekday'
        hour_24 = timestamp.strftime('%H')
        hour_12 = timestamp.strftime('%I')
        minute = timestamp.strftime('%M')
        am_pm = timestamp.strftime('%p')

        return {
            "Formatted_Date": formatted_date,
            "Formatted_Time": formatted_time,
            "Day_of_Month": day_of_month,
            "Month": month,
            "Year": year,
            "Day_of_Week": day_of_week,
            "Week_Number": week_number,
            "Date_Type": date_type,
            "Hour_24_Format": hour_24,
            "Hour_12_Format": hour_12,
            "Minute": minute,
            "AM_PM": am_pm
        }

    def apply_keyword_matching(self, row):
        """
        Applies keyword matching to a row of data to update themes, subthemes, and subsubthemes.

        Args:
            row (pd.Series): The row of data to be processed.

        Returns:
            pd.Series: The row with updated themes, subthemes, and subsubthemes.
        """
        data = self.keywords
        keyword_data = data.drop('_id', axis=1, errors='ignore')
        text = row['Message']
        theme, subtheme, subsubtheme = self.update_themes_subthemes(text, keyword_data)
        if theme is not None and subtheme is not None and subsubtheme is not None:
            row['Themes'] = theme
            row['Subthemes'] = subtheme
            row['Subsubthemes'] = subsubtheme
        return row

    def calculate_match_percentage(self, message1, message2):
        """
        Calculates the match percentage between two messages based on common words.

        Args:
            message1 (str): The first message.
            message2 (str): The second message.

        Returns:
            float: The match percentage between the two messages.
        """
        if pd.isna(message1) or pd.isna(message2):
            return 0.0

        words1 = set(message1.split())
        words2 = set(message2.split())

        if len(words1) == 0:
            return 0.0

        common_words = words1.intersection(words2)
        return len(common_words) / len(words1)

    def categorize_duplicates(self, new_data, column_to_check="Message", match_threshold=0.8):
        """
        Categorizes duplicate entries in the DataFrame based on a match threshold.

        Args:
            new_data (pd.DataFrame): The DataFrame containing the data to be categorized.
            column_to_check (str): The column to check for duplicates.
            match_threshold (float): The threshold for considering entries as duplicates.

        Returns:
            pd.DataFrame: The DataFrame with categorized duplicates.
        """
        new_data['Tag'] = True
        categorized_statements = set()
        uncategorized_statements = set(new_data.index)

        while len(uncategorized_statements) > 0:
            statement1_index = uncategorized_statements.pop()
            statement1 = new_data.at[statement1_index, column_to_check]
            duplicate_indices = set()

            for statement2_index in list(uncategorized_statements):
                statement2 = new_data.at[statement2_index, column_to_check]
                match_percentage = self.calculate_match_percentage(statement1, statement2)

                if match_percentage >= match_threshold:
                    duplicate_indices.add(statement2_index)

            if len(duplicate_indices) > 0:
                categorized_statements.add(statement1_index)
                for duplicate_index in duplicate_indices:
                    uncategorized_statements.remove(duplicate_index)
                    new_data.at[duplicate_index, 'Tag'] = False

        return new_data