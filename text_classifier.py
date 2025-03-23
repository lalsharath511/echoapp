from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
import re
import nltk
import pickle
import pandas as pd
from datetime import datetime

# Download necessary NLTK datasets
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


class TextClassifier:
    def __init__(self, training_data=None):
        """
        Initializes the TextClassifier class with optional training data.

        Args:
            training_data (pd.DataFrame, optional): The training data to be used for model training. Defaults to None.
        """
        self.training_data = training_data
        self.tfidf_vectorizer = TfidfVectorizer()
        self.gb_classifier = GradientBoostingClassifier(n_estimators=100, random_state=42)

    def clean_text(self, text):
        """
        Cleans and preprocesses the input text by converting it to lowercase, removing special characters,
        tokenizing, removing stopwords, and lemmatizing the tokens.

        Args:
            text (str): The input text to be cleaned.

        Returns:
            str: The cleaned and preprocessed text.
        """
        if pd.notna(text):
            text = text.lower()  # Convert text to lowercase
            text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters
            tokens = word_tokenize(text)  # Tokenize the text
            stop_words = set(stopwords.words('english'))  # Get English stopwords
            tokens = [token for token in tokens if token not in stop_words]  # Remove stopwords
            lemmatizer = WordNetLemmatizer()  # Initialize lemmatizer
            tokens = [lemmatizer.lemmatize(token) for token in tokens]  # Lemmatize tokens
            cleaned_text = ' '.join(tokens)  # Join tokens back into a single string
            return cleaned_text
        else:
            return ''  # Return empty string for NaN values

    @staticmethod
    def load_model(file_path='model_q2.pkl'):
        """
        Loads a pre-trained model from a specified file path.

        Args:
            file_path (str, optional): The path to the model file. Defaults to 'model_q2.pkl'.

        Returns:
            dict: The loaded model containing the TF-IDF vectorizer and classifier.
        """
        with open(file_path, 'rb') as model_file:
            model_bytes = model_file.read()  # Read the model file
        loaded_model = pickle.loads(model_bytes)  # Deserialize the model
        return loaded_model

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
            keyword = keyword.lower().replace('#', '')  # Normalize keyword
            if keyword in text.lower():  # Check if keyword exists in the text
                return theme, subtheme, None
        return None, None, None

    def train_classifier(self):
        """
        Trains the Gradient Boosting Classifier using the provided training data.

        Raises:
            ValueError: If training data is not provided or required columns are missing.
        """
        if self.training_data is None:
            raise ValueError("Training data is not provided.")

        data = pd.DataFrame(self.training_data)

        # Check for required columns
        required_columns = ['Vernon Sub Sub Theme', 'Vernon Sub Theme', 'Vernon Main Theme', 'Message']
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Drop rows with missing values in required columns
        data = data[pd.notnull(data['Vernon Sub Sub Theme'])]
        data = data[pd.notnull(data['Vernon Sub Theme'])]
        data = data[pd.notnull(data['Vernon Main Theme'])]
        data = data[pd.notnull(data['Message'])]

        # Clean the text data
        data['Message'] = data['Message'].apply(self.clean_text)

        # Fit the TF-IDF vectorizer and transform the text data
        self.tfidf_vectorizer.fit(data['Message'])
        data_tfidf = self.tfidf_vectorizer.transform(data['Message'])

        # Combine themes into a single column for multi-label classification
        data['Combined Themes'] = data['Vernon Main Theme'] + '||' + data['Vernon Sub Theme'] + '||' + data['Vernon Sub Sub Theme']

        # Train the Gradient Boosting Classifier
        self.gb_classifier.fit(data_tfidf, data['Combined Themes'])

    def auto_save_locally(self):
        """
        Automatically saves the trained model locally with a timestamped filename.
        """
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get current timestamp
        file_path = f"model/model_{current_datetime}.pkl"  # Define file path

        # Ensure the model is trained before saving
        self.train_classifier()

        # Prepare model data for saving
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'gb_classifier': self.gb_classifier
        }

        # Save the model to the specified file path
        with open(file_path, 'wb') as model_file:
            pickle.dump(model_data, model_file)

        print(f"Model saved locally at {file_path}")