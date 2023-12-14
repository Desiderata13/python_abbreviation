import re
import itertools as it
import pandas as pd


# Function to read a file and save each line as a list.
def read_file():
    lines_list = []
    read_file.filename = input("Please enter the file name: ")
    f = read_file.filename + ".txt"

    try:
        # Open the file and read its content
        with open(f, "r") as file_words:
            lines = file_words.read()
            lines_list = lines.splitlines()
    except FileNotFoundError:
        print("The file you entered is not found.")

    return lines_list


# Function to clean each name by removing all characters & replacing '-' to space
def clean_words():
    lines_list = read_file()
    original_words = lines_list

    # Process each word in the list
    lines_list = [word.upper() for word in lines_list]  # making all letters to upper case
    lines_list = [word.replace("-", " ") for word in lines_list]  # replacing - to space
    lines_list = [re.sub(r"[^\w\s]", '', word) for word in lines_list]  # ignoring all other characters

    # Create a dictionary mapping cleaned words to original words
    clean_words.orig_word_dict = {lines_list[i]: original_words[i] for i in range(len(lines_list))}

    return lines_list


# Function to get all possible 3-letter combinations for each name.
def create_abbreviations():
    lines_list = clean_words()
    abbreviation_list = []
    abbreviation_dict = {}

    # Iterate through each word in the list
    for word in lines_list:
        # Remove spaces from the word
        word_without_spaces = word.replace(" ", "")

        # Generate all possible 3-letter combinations
        for (a, b, c) in it.combinations(word_without_spaces, 3):
            abbreviation_list.append(a + b + c)

        # Remove duplicates by converting the list to a set
        abbreviation_set = set(abbreviation_list)

        # Convert the set back to a list and store in the dictionary
        abbreviation_dict[word] = list(abbreviation_set)

        # Reset the list for the next word
        abbreviation_list = []

    return abbreviation_dict


# Function to calculate the score for each acronym of words.
def calculate_score(acr_dict):
    # Read the values from the file
    with open("values.txt", "r") as val:
        values = {k: v for k, v in map(str.split, val)}

    score = 0
    full_list = []

    # Iterate through each word and its acronyms
    for words, acr_list in acr_dict.items():
        wordlist = words.split()

        # Iterate through each acronym
        for acr in acr_list:
            flag = 0
            pos1 = wordlist[0].find(acr[0])

            # Check the position of the first character in the first word
            if pos1 == 0:
                score = score + 0
            else:
                score = score + 10000

            # Iterate through each word in the list
            for w in range(0, len(wordlist)):
                temp_word = wordlist[w]

                # Modify the first character of the first word if needed
                if pos1 == 0 and w == 0:
                    temp_word = temp_word[:pos1] + "#" + temp_word[pos1 + 1:]

                # Check the position of the second character
                pos2 = temp_word.find(acr[1])

                if pos2 == 0:
                    score = score + 0
                    flag = 3
                    temp_word = temp_word[:pos2] + "#" + temp_word[pos2 + 1:]
                elif pos2 == len(wordlist[w]) - 1 and flag != 3:
                    if acr[1] != 'E':
                        score = score + 5
                        flag = 1
                        temp_word = temp_word[:pos2] + "#" + temp_word[pos2 + 1:]
                    else:
                        score = score + 20
                        flag = 1
                        temp_word = temp_word[:pos2] + "#" + temp_word[pos2 + 1:]
                elif (pos2 in [1, 2]) and flag != 3:
                    score = score + pos2 + int(values.get(acr[1], 0))
                    flag = 1
                    temp_word = temp_word[:pos2] + "#" + temp_word[pos2 + 1:]
                elif pos2 >= 3 and flag != 3:
                    score = score + 3 + int(values.get(acr[2], 0))
                    flag = 1
                    temp_word = temp_word[:pos2] + "#" + temp_word[pos2 + 1:]

                # Check the position of the third character
                if pos2 != -1:
                    temp_word1 = temp_word[pos2:]
                    pos3 = temp_word1.find(acr[2])
                else:
                    pos3 = temp_word.find(acr[2])

                # Process the third character
                if pos3 != -1 and flag != 0:
                    if temp_word.find(acr[2]) == len(temp_word) - 1:
                        if acr[2] != 'E':
                            score = score + 5
                        else:
                            score = score + 20
                    elif temp_word.find(acr[2]) == 1:
                        score = score + 1 + int(values.get(acr[2], 0))
                    elif temp_word.find(acr[2]) == 2:
                        score = score + 2 + int(values.get(acr[2], 0))
                    elif temp_word.find(acr[2]) >= 3:
                        score = score + 3 + int(values.get(acr[2], 0))
                    elif temp_word.find(acr[2]) == 0:
                        score = score + 0

            # Create a new list with word, acronym, and score
            new_list = [clean_words.orig_word_dict[words], acr, score]
            full_list.append(new_list)
            score = 0

    # Create a DataFrame from the list of scores
    acr_df = pd.DataFrame(full_list, columns=["words", "acr", "score"])
    return acr_df


# Function to find the best acronym for each word
def find_best_acronym(acr_df):
    # Create a copy of the DataFrame with relevant columns
    acr_df_copy = acr_df[['words', 'acr', 'score']].copy()

    # Add a new column 'rank' based on the score's rank within each word group
    acr_df_copy['rank'] = acr_df_copy.groupby('words')['score'].rank(ascending=True)

    # Ensure that each word has at least one abbreviation
    acr_df_copy.loc[acr_df_copy.groupby('words')['rank'].idxmin(), 'rank'] = 1

    # Filter the DataFrame to keep only the rows with the best acronym for each word
    acr_df_copy = acr_df_copy[acr_df_copy['rank'] == 1]

    # Keep only the columns 'words' and 'acr', and sort the DataFrame by index
    acr_df_copy = acr_df_copy[['words', 'acr']].sort_index()

    return acr_df_copy


# Main function to save the output as csv
def main():
    acr_dict = create_abbreviations()
    acr_df = calculate_score(acr_dict)
    acr_df_full = find_best_acronym(acr_df)
    output_name = 'li_' + read_file.filename + '_abbrevs.txt'
    acr_df_full.to_csv(output_name, sep='\n', encoding='utf-8', index=False, header=False)

if __name__ == "__main__":
    main()
