import pandas as pd
from datetime import datetime
from dateutil import parser
import math
from settings import *  # Ensure this import is properly configured in your environment

class FieldMapper:
    def __init__(self, file_path):
        """
        Initializes the FieldMapper class with the file path and sets up necessary attributes.

        Args:
            file_path (str): The path to the file to be processed.
        """
        self.file_path = file_path
        self.field_mapping = {}
        self.source = None
        self.item = []

    def read_file(self):
        """
        Reads the file from the provided path and returns it as a pandas DataFrame.

        Returns:
            pd.DataFrame: The DataFrame containing the file data.

        Raises:
            ValueError: If the file format is unsupported.
            RuntimeError: If there is an error reading the file.
        """
        try:
            if self.file_path.endswith('.xlsx'):
                return pd.read_excel(self.file_path)
            elif self.file_path.endswith('.csv'):
                return pd.read_csv(self.file_path)
            else:
                raise ValueError("Unsupported file format. Only .xlsx and .csv are supported.")
        except Exception as e:
            raise RuntimeError(f"Error reading file: {str(e)}")

    def format_timestamp_auto(self, input_timestamp_str):
        """
        Automatically detects and formats the timestamp string into a standardized format.

        Args:
            input_timestamp_str (str): The timestamp string to be formatted.

        Returns:
            str: The formatted timestamp string in "dd-mm-yyyy HH:MM:SS" format, or None if the input is invalid.

        Raises:
            ValueError: If the timestamp format cannot be determined.
        """
        try:
            if isinstance(input_timestamp_str, pd.Timestamp):
                input_timestamp_str = input_timestamp_str.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(input_timestamp_str, str) and input_timestamp_str.lower() != "nan":
                possible_formats = [
                    "%Y-%m-%dT%H:%M:%S.%fZ",  # Example: 2024-03-11T10:15:30.123Z
                    "%m/%d/%Y %H:%M",         # Example: 03/11/2024 10:15
                    "%m/%d/%Y %H:%M:%S",      # Example: 03/11/2024 10:15:30
                    "%d-%m-%Y %H:%M",         # Example: 21-01-2025 18:00
                    "%d-%m-%Y %H:%M:%S",      # Example: 21-01-2025 18:00:29
                    "%Y-%m-%d %H:%M:%S"       # Example: 2025-01-14 17:12:54
                ]

                for timestamp_format in possible_formats:
                    try:
                        dt_object = datetime.strptime(input_timestamp_str, timestamp_format)
                        return dt_object.strftime("%d-%m-%Y %H:%M:%S")
                    except ValueError:
                        continue

                dt_object = parser.parse(input_timestamp_str)
                return dt_object.strftime("%d-%m-%Y %H:%M:%S")
            else:
                return None
        except ValueError as e:
            raise ValueError(f"Unable to determine timestamp format: {str(e)}")

    def detect_source(self, df):
        """
        Detects the source of the data based on the columns present in the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to analyze.

        Raises:
            ValueError: If the source cannot be determined.
            RuntimeError: If there is an error during detection.
        """
        try:
            if all(field in df.columns for field in RIVAL_IQ):
                self.source = 'Rival IQ'
            elif all(field in df.columns for field in PHANTOM_BUSTER):
                self.source = 'Phantom Buster'
            else:
                raise ValueError("Unable to determine the source file.")
        except Exception as e:
            raise RuntimeError(f"Error detecting source: {str(e)}")

    def map_fields(self, df):
        """
        Maps the fields from the source DataFrame to a standardized format based on the detected source.

        Args:
            df (pd.DataFrame): The DataFrame containing the raw data.

        Returns:
            list: A list of dictionaries, where each dictionary represents a mapped record.
        """
        data_dict = df.to_dict(orient='records')
        self.item = []

        if self.source == 'Rival IQ':
            for data in data_dict:
                engagement = (
                    data.get('applause', 0) +
                    data.get('conversation', 0) +
                    data.get('amplification', 0)
                )
                bucket = self._get_engagement_bucket(engagement)
                company_name = COMPANY_MAPPING.get(data['company'].lower(), data['company'].capitalize())
                original_datetime = self.format_timestamp_auto(data['published_at'])
                post_type = self._get_post_type(data['post_type'])
                handle_name = self._get_handle_name(data['presence_handle'], company_name, data['channel'])
                message = self._get_message(data['message'], data['link_title'])

                self.field_mapping = {
                    'Publish Date / Time': original_datetime,
                    'Company Name': company_name,
                    'Social Media Channel': data['channel'],
                    'Handle Name': handle_name,
                    'Message': message,
                    'Link': data['post_link'],
                    'Docu_Link': data['link'],
                    'Image': data['image'],
                    'Post Type': post_type,
                    'Like / applause': data['applause'],
                    'Comment / conversation': data['conversation'],
                    'Share / Repost / amplification': data['amplification'],
                    'Engagement': engagement,
                    "engagement_bucket": bucket,
                    'Video Views': data['video_views'],
                    'View Views bucket': '',
                    'Video Duration': '',
                    'Video Type': '',
                    'audience': data['audience'],
                }
                self.item.append(self.field_mapping)

        elif self.source == 'Phantom Buster':
            for data in data_dict:
                company_name = self._get_company_name(data.get('profileUrl', ''))
                post_type = self._get_post_type(data['type'])
                engagement = (
                    data.get('likeCount', 0) +
                    data.get('commentCount', 0) +
                    data.get('repostCount', 0)
                )
                bucket = self._get_engagement_bucket(engagement)
                original_datetime = self.format_timestamp_auto(data['postTimestamp'])

                self.field_mapping = {
                    'Publish Date / Time': original_datetime,
                    'Company Name': company_name,
                    'Social Media Channel': 'LinkedIn',
                    'Handle Name': company_name,
                    'Message': data['postContent'],
                    'Link': data['postUrl'],
                    'Docu_Link': "",
                    'Image': data['imgUrl'],
                    'Post Type': post_type,
                    'Like / applause': data['likeCount'],
                    'Comment / conversation': data['commentCount'],
                    'Share / Repost / amplification': data['repostCount'],
                    'Engagement': engagement,
                    "engagement_bucket": bucket,
                    'Video Views': '',
                    'Video Duration': '',
                    'View Views bucket': '',
                    'Video Type': '',
                    'audience': '',
                }
                self.item.append(self.field_mapping)

        return self.item

    def _get_engagement_bucket(self, engagement):
        """
        Determines the engagement bucket based on the engagement value.

        Args:
            engagement (int): The engagement value.

        Returns:
            str: The engagement bucket.
        """
        if 0 <= engagement <= 100:
            return '0-100 Engagement'
        elif 101 <= engagement <= 500:
            return '101-500 Engagement'
        elif 501 <= engagement <= 1000:
            return '501-1000 Engagement'
        elif engagement > 1000:
            return '1000+ Engagement'
        return None

    def _get_post_type(self, post_type):
        """
        Determines the post type based on the raw post type value.

        Args:
            post_type (str): The raw post type value.

        Returns:
            str: The standardized post type.
        """
        if post_type.lower() == "photo":
            return "Image"
        elif "video (linkedin source)" in post_type.lower():
            return "Video"
        else:
            return post_type.capitalize()

    def _get_handle_name(self, presence_handle, company_name, channel):
        """
        Determines the handle name based on the presence handle, company name, and channel.

        Args:
            presence_handle (str): The raw presence handle.
            company_name (str): The company name.
            channel (str): The social media channel.

        Returns:
            str: The standardized handle name.
        """
        if channel == "YouTube":
            return YOUTUBE_MAPPING.get(company_name, company_name)
        return str(presence_handle).capitalize() if presence_handle else ""

    def _get_message(self, message, link_title):
        """
        Determines the message based on the raw message and link title.

        Args:
            message (str): The raw message.
            link_title (str): The link title.

        Returns:
            str: The standardized message.
        """
        if isinstance(message, float) and math.isnan(message):
            return link_title
        return message

    def _get_company_name(self, profile_url):
        """
        Determines the company name based on the profile URL.

        Args:
            profile_url (str): The profile URL.

        Returns:
            str: The standardized company name.
        """
        company_name = str(profile_url).strip("/").strip()
        if not company_name or company_name.lower() == 'nan':
            return "Unknown"
        return COMPANY_MAPPING.get(company_name.lower(), company_name.capitalize())