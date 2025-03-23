from config import GPT_API_KEY
import openai
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

class EntityProcessor:
    def __init__(self):
        """
        Initializes the EntityProcessor class by setting up the OpenAI API key and defining the entity types to extract.
        """
        openai.api_key = GPT_API_KEY
        self.entity_types = ["Person Names", "Organization", "Hash Tags", "Location", "Brand", "Category", "URLs"]

    def extract_entities(self, message):
        """
        Extracts entities from a given message using OpenAI's GPT-3.5-turbo-instruct model.

        Args:
            message (str): The text message from which entities need to be extracted.

        Returns:
            dict: A dictionary containing the extracted entities for each entity type, or None if an error occurs.
        """
        try:
            prompt = f"Please extract the following entity types from the text: {', '.join(self.entity_types)}. \n\nText: {message}"
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.5,
            )
            entities = response["choices"][0]["text"].split("\n")
            entity_dict = {et: None for et in self.entity_types}
            for entity in entities:
                for et in self.entity_types:
                    if et in entity:
                        entity_dict[et] = entity.split(":")[1].strip()
            return entity_dict
        except Exception as e:
            print(f"Error during entity extraction: {e}")
            return None

    def process_entities(self, df, chunk_size=50):
        """
        Processes a DataFrame to extract entities in parallel using chunks for efficient processing.

        Args:
            df (pd.DataFrame): The DataFrame containing the messages to process.
            chunk_size (int): The size of each chunk for parallel processing.

        Returns:
            pd.DataFrame: The DataFrame with extracted entities added as new columns.
        """
        try:
            chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(self.apply_extraction, chunks))
            df = pd.concat(results, ignore_index=True)
            df = df.dropna(subset=['extracted_entities'])
            entity_df = pd.DataFrame(df['extracted_entities'].tolist(), columns=self.entity_types)
            df = pd.concat([df, entity_df], axis=1)
            return df
        except Exception as e:
            print(f"Error during entity processing: {e}")
            return df  # Return the original DataFrame if an error occurs

    def apply_extraction(self, chunk):
        """
        Applies entity extraction to a chunk of the DataFrame.

        Args:
            chunk (pd.DataFrame): A subset of the DataFrame to process.

        Returns:
            pd.DataFrame: The chunk with extracted entities added as a new column.
        """
        chunk = chunk.copy()
        chunk['extracted_entities'] = chunk['Message'].apply(self.extract_entities)
        return chunk