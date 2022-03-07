# %%
import re

from nltk import word_tokenize

# %%
pat1 = "@[^ ]+"
pat2 = "http[^ ]+"
pat3 = "www.[^ ]+"
pat4 = "#[^ ]+"
pat5 = "[0-9]"
combined_pat = "|".join((pat1, pat2, pat3, pat4, pat5))

pat6 = "^[^a-zA-Z]*"


# tweet = '@ozan__caglayan ? you always do early stopping based on validation data  '
tweet = "@Caenorst @elonmusk 100?? that still leaves 9.7 hours for leisure and sleep.  "
tweet = "#fastbert 1.5.0 supports new model architectures - albert, camembert and the exciting distilroberta.\n\nsupports @huggingface #transformers v2.2\n\nhttps://github.com/kaushaltrivedi/fast-bert/releases/tag/v1.5.0"
tweet = tweet.lower()

stripped = re.sub(combined_pat, "", tweet)
print(stripped)
stripped = re.sub(pat6, "", stripped)
print(stripped)
tokens = word_tokenize(stripped)
words = [x for x in tokens if len(x) > 1]
sentences = " ".join(words)
negations = re.sub("n't", "not", sentences)


# %%
