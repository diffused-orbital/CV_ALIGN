import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn

nltk.download('wordnet')
nltk.download('punkt_tab')
nltk.download('stopwords')


def tokenize_section(text: str) -> list:
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text.lower())
    keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
    #print(keywords,"\n")
    return keywords

def tokenize_sections(sections: dict) -> dict:
    return {sec: tokenize_section(text) for sec, text in sections.items()}