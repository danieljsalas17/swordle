import pandas as pd
import numpy as np
from collections import Counter
import pkg_resources
import wordle_solver

DATA_PATH = 'data/sgb.txt'

class HardModeSolver:
    def __init__(self, wordbank: str=DATA_PATH, n_letters: int=5, score: str='across', verbose: bool=False):
        '''
        HardModeSolver solves a Wordle puzzle in "hard mode", i.e., no guessing with disjoint sets of characters between guesses.
        
        INPUT
        -----
        wordbank: str, path/to/wordbank.[txt/csv]
            - path to single column file read by pandas.read_csv, no header.
        '''
        self.wordbank_path = wordbank
        self.n_letters = n_letters
        self.score = score
        self.verbose = verbose

        # load wordbank dataframe, calculate features, empty guesses & results
        self.reset()

    def reset(self) -> None:
        stream = pkg_resources.resource_stream(wordle_solver.__name__, DATA_PATH)
        self.wordbank = pd.read_csv(stream, header=None)
        self.wordbank.columns = ['word']
        self.wordbank['no_green_word'] = self.wordbank.word
        self.green_letters = {}
        self.wordbank_features()
        self.guesses = []
        self.results = []

    def status(self) -> None:
        print('Status')
        for i, (guess, result) in enumerate(zip(self.guesses, self.results)):
            print(f'Guess {i+1}: {guess} => {result}')

    def guess(self) -> str:
        guess = self.wordbank.sort_values(by=f'{self.score}_score', ascending=False).iloc[0,0]
        n_choices = self.wordbank.shape[0]
        self.guesses.append(guess)
        if self.verbose:
            print(f'Guess: {guess}. Best choice of {n_choices} words available.')
        return guess

    def wordbank_features(self) -> None:
        self.wordbank = self.wordbank[['word','no_green_word']].copy()

        # count frequency of letters in each word position. Used to rank guesses.
        self.letter_counts = {}
        for i in range(self.n_letters):
            letter = f'letter_{i+1}'
            if i not in self.green_letters:
                # new column for letter
                self.wordbank[f'letter_{i+1}'] = self.wordbank.word.apply(lambda x: x[i])
                # count occurrences of each letter in position `i`
                self.letter_counts[letter] = Counter(self.wordbank[letter])
                # add column for position count, will be used for ranking guesses.
                self.wordbank[f'count_{i+1}'] = self.wordbank[letter].map(self.letter_counts[letter])
            else:
                # skip previous green letters
                self.wordbank[f'letter_{i+1}'] = '_'
                self.letter_counts[letter] = dict()
                self.wordbank[f'count_{i+1}'] = 0

        
        # count letters across positions in word. 
        across = {'_': 0}
        for letter, letter_count in self.letter_counts.items():
            for l, n in letter_count.items():
                if l not in across:
                    across[l] = n
                else:
                    across[l] += n

        # check if repeated character (left to right). store this value in wordbank.
        self.wordbank['repeat_1'] = False
        for i in range(1,self.n_letters):
            prev_letters = [f'letter_{j+1}' for j in range(i)]
            letter = f'letter_{i+1}'
            self.wordbank[f'repeat_{i+1}'] = \
                (self.wordbank.loc[:, prev_letters].values == self.wordbank.loc[:,[letter]].values).any(axis=1)
                    
        # save across counts to wordbank, will be used for ranking guesses
        for i in range(self.n_letters):
            self.wordbank[f'across_{i+1}'] = self.wordbank[f'letter_{i+1}'].map(across)

        # Scores for each word, used for ranking words
        # total counts of common inplace characters
        self.wordbank['inplace_score'] = self.wordbank[[f'count_{i+1}' for i in range(self.n_letters)]].sum(axis=1)

        # total counts of characters in word across other words (regardless of position)
        self.wordbank['across_score'] = \
            (
                self.wordbank[[f'across_{i+1}' for i in range(self.n_letters)]].values \
              * (~self.wordbank[[f'repeat_{i+1}' for i in range(self.n_letters)]].values)
            ).sum(axis=1).astype(int)

        # combined score (equal weight, can explore differences later)
        self.wordbank['combined_score'] = self.wordbank['inplace_score'] + self.wordbank['across_score']

    
    def load_result(self, result: str) -> None:
        '''
        Purpose of loading the result from Wordle is to update our choices, i.e., 
        filter the wordbank and recalculate features & scores.

        INPUT
        -----
        result: str
            - string consisting of "G", "Y", "K"
        '''
        self.results.append(result)
        last_guess = self.guesses[-1]

        key_cols = ['word', 'no_green_word'] + [f'letter_{i+1}' for i in range(self.n_letters)]
        self.wordbank = self.wordbank[key_cols].copy()

        # hard-mode filtering
        for i, (g, r) in enumerate(zip(last_guess, result)):
            # select only words with same green character. filter out green letters for future.
            if i in self.green_letters:
                continue
            elif r == 'G':
                self.wordbank = self.wordbank[self.wordbank[f'letter_{i+1}'] == g].copy()
                self.green_letters[i] = g
                self.wordbank['no_green_word'] = self.wordbank['no_green_word'].str.slice_replace(i,i+1,'_')
            # filter out black/white characters
            elif r == 'K':
                self.wordbank = self.wordbank[self.wordbank['no_green_word'].apply(lambda x: g not in x)].copy()
            # filter for words with yellow letter in word, but not in current position
            else:
                self.wordbank = self.wordbank[
                    (self.wordbank['no_green_word'].apply(lambda x: g in x)) \
                  & (self.wordbank[f'letter_{i+1}'] != g)
                ].copy()

        # refresh wordbank features and scores
        self.wordbank_features()    
    
if __name__=='__main__':
    from wordle_solver.simulator import WordleSimulator

    word = 'baste'

    HMS = HardModeSolver(verbose=True)
    Wordle = WordleSimulator(word)

    print('Starting default Wordle game.')
    while not Wordle.done:
        guess = HMS.guess()
        print(HMS.wordbank.sort_values(by='across_score', ascending=False).head().T)
        result = Wordle.guess(guess)
        HMS.load_result(result)
