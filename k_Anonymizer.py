import re
import pandas as pd

# def anonymize_text(text, words_to_anonymize, code_format="[XXX_{}]", case_insensitive=True):
#     anonymized_text = text
#     word_to_code = {}
#     code_replacements = {}

#     # Create unique codes for each word/entity
#     for i, word in enumerate(words_to_anonymize):
#         code = code_format.format(i + 1)
#         word_key = word.lower() if case_insensitive else word
#         word_to_code[word_key] = code
#         code_replacements[code] = 0

#     # Function to replace words/entities with codes
#     def replace_with_code(match):
#         word = match.group(0)
#         word_key = word.lower() if case_insensitive else word
#         code = word_to_code[word_key]
#         code_replacements[code] += 1
#         return code

#     # Replace each word/entity with its corresponding code
#     for word in words_to_anonymize:
#         regex_flags = re.IGNORECASE if case_insensitive else 0
#         # Escape the word to handle special characters and use word boundaries for accurate matching
#         pattern = re.escape(word)
#         anonymized_text, replacements = re.subn(pattern, replace_with_code, anonymized_text, flags=regex_flags)
#         print(f"Pattern: {pattern}, Replacements: {replacements}")

#     # Create a DataFrame to display the replacement statistics
#     replacement_stats = pd.DataFrame(list(code_replacements.items()), columns=['Code', 'Replacements'])

#     return anonymized_text, word_to_code, replacement_stats

# # Example usage
# text = "Alice works at Acme Corp. She lives at 123 Main St. Alice loves working at Acme Corp."
# words_to_anonymize = ["Alice", "Acme Corp", "123 Main St"]

# anonymized_text, word_to_code, replacement_stats = anonymize_text(text, words_to_anonymize)

# print("\nAnonymized Text:")
# print(anonymized_text)

