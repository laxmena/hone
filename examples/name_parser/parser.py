def parse_names(text: str) -> list[str]:
    """
    Extracts names from a given text.
    Currently uses a very naive approach of returning any capitalized word.
    """
    names = []
    for word in text.split():
        # Remove punctuation
        clean_word = "".join(c for c in word if c.isalpha())
        if clean_word.istitle():
            names.append(clean_word)
    return names

if __name__ == "__main__":
    sample = "My name is Arthur Pendragon and my friend is Merlin. We live in Camelot, but we visit London sometimes."
    print("Extracted:", parse_names(sample))
