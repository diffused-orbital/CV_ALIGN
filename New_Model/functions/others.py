import re
import json
import nltk
from nltk.corpus import wordnet as wn

# Load once
nltk.download('wordnet')
default_synonyms = {
    "ml": ["machine learning", "ml"],
    "ai": ["artificial intelligence", "ai"],
    "nlp": ["natural language processing", "nlp"],
    "data analysis": ["data analytics", "data analysis"]
}

with open('synonym_dict.json', 'w') as f:
    json.dump(default_synonyms, f)

def create_synonym_mapping(text, json_mapping_file='synonym_dict.json'):
    # Load JSON-based dictionary (custom synonyms)
    with open(json_mapping_file, 'r') as f:
        json_mapping = json.load(f)
    
    synonym_mapping = {}
    
    # Add JSON synonyms
    for key, synonyms in json_mapping.items():
        for synonym in synonyms:
            synonym_mapping.setdefault(key, []).append(synonym)

    # WordNet synonyms
    words = set(re.findall(r'\b\w+\b', text.lower()))
    for word in words:
        synsets = wn.synsets(word)
        for synset in synsets:
            for lemma in synset.lemma_names():
                if lemma.lower() != word:
                    synonym_mapping.setdefault(word, []).append(lemma.lower())
    
    # Remove duplicates
    for key in synonym_mapping:
        synonym_mapping[key] = list(set(synonym_mapping[key]))

    return synonym_mapping


def apply_synonym_mapping(text, synonym_mapping):
    for key, synonyms in synonym_mapping.items():
        for synonym in synonyms:
            pattern = r'\b{}\b'.format(re.escape(synonym))
            text = re.sub(pattern, key, text, flags=re.IGNORECASE)
    return text

def flatten_to_text(sections):
    if isinstance(sections, dict):
        return ' '.join(flatten_to_text(v) for v in sections.values())
    elif isinstance(sections, list):
        return ' '.join(flatten_to_text(v) for v in sections)
    else:
        return str(sections)
