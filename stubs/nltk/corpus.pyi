"""Typing for nltk.corpus module"""

# corpus.pyi
from typing import List

# Define the words function
class words:
    @staticmethod
    def words() -> List[str]: ...
