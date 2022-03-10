# Author: Daniel Salas
from getpass import getpass
import pandas as pd
import os

HOME = os.environ['HOME']
WORDLE = 'Projects/wordle-solver'
DATA = 'data/alpha.txt'
SRC = 'wordle_solver/src/'
ALPHA = os.path.join(HOME,WORDLE,DATA)

# TODO
# 1: Reject words not in word list or not same length
# 2: Print out available characters by letter block
# 3: Force lower case

N_CHAR = 40

def wrap_color(string: str, color_code: str) -> str:
    wrapped_string = f'\x1b[{color_code}m{string}\x1b[0m'
    return wrapped_string

class WordleSimulator:
    def __init__(self, word: str='ratio', max_guesses: int=6, verbose: bool=True):
        '''
        WordleSimulator allows you to play Wordle. You provide the mystery word, and then make guesses. 
        G = green, Y = yellow, K = black. Wordle is typically 5 letter words, but this can be more or less if you chose. 
        '''
        if word is not None:
            self.word = word
        self.n_guesses = 0
        self.max_guesses = max_guesses
        self.results = []
        self.unicode_results = []
        self.alpha_blocks_results = []
        self.done = False
        self.verbose = verbose
        self.blocks_unicode = {
            'G' : '\U0001F7E9', # green block emoji unicode
            'Y' : '\U0001F7E8', # yellow block emoji unicode
            'K' : "\u2B1B"      # black block emoji unicode
        }
        self.blocks_cc = {
            'G': '1;1;42', # green block, white text
            'Y': '1;1;43', # yellow block, white text
            'K': '1;1;40', # black block, white text
        }
        self.alphabet = list('qwertyuiopasdfghjklzxcvbnm')
        self.chosen_alphabet = {
            'G': [],
            'Y': [],
            'K': []
        }
    
    def convert_unicode(self, result: str) -> str:
        unicode_result = "".join([self.blocks_unicode[c] for c in  list(result)])
        return unicode_result
    
    def convert_alpha_blocks(self, guess: str, result: str) -> str:
        alpha_blocks = list(guess.upper())
        for i, (G, R) in enumerate(zip(list(guess.upper()), list(result))):
            color_code = self.blocks_cc[R]
            self.chosen_alphabet[R].append(G.lower())
            alpha_blocks[i] = f'\x1b[{color_code}m {G} \x1b[0m'
        return "".join(alpha_blocks)

    def print_alphabet(self) -> None:
        colored_alphabet = [l for l in self.alphabet]
        for i, letter in enumerate(self.alphabet):

            if letter in self.chosen_alphabet['G']:
                cc = self.blocks_cc['G']
            elif letter in self.chosen_alphabet['Y']:
                cc = self.blocks_cc['Y']
            elif letter in self.chosen_alphabet['K']:
                cc = self.blocks_cc['K']
            else:
                cc = '1;30;47' # default white block w/ black text
            
            colored_alphabet[i] = f'\x1b[{cc}m {letter} \x1b[0m'
        
        stack_slices = [(0,10), (10,19), (19,26)] # stack alphabet
        print("\n\n")
        # print('Keyboard'.center(N_CHAR))
        for i, ss in enumerate(stack_slices):
            print(" " * (int(2*i + 1) + int(N_CHAR/2 - 17)), "".join(colored_alphabet[ss[0]:ss[1]]))
        print("\n")

            
    def guess(self, word: str) -> str:
        guess = word.lower()

        # keep track of guesses
        self.n_guesses += 1
        if self.n_guesses == self.max_guesses:
            self.done = True
        
        # collect results
        if self.n_guesses <= self.max_guesses:

            result = self._result(guess)
            unicode_result = self.convert_unicode(result)
            alpha_blocks_result = self.convert_alpha_blocks(guess, result)

            self.results.append(result)
            self.unicode_results.append(unicode_result)
            self.alpha_blocks_results.append(alpha_blocks_result)
            
            if self.verbose:
                print('-' * N_CHAR)
                print(f'ATTEMPT {self.n_guesses}/{self.max_guesses}'.center(N_CHAR))
                print('-' * N_CHAR, "\n")
                for abr in self.alpha_blocks_results:
                    print(" " * int(N_CHAR/2 - 8), abr)
                self.print_alphabet()
                print('*' * N_CHAR)

        # phony result when attempts > allowed
        elif self.done:
            self.done = True
            if self.verbose:
                print('NO MORE GUESSES')
            result = 'XXXXX'

        else:
            print('NO MORE GUESSES')
            result = 'XXXXX'

        # end game
        if all([r == 'G' for r in list(result)]):
            self.done = True
            if self.verbose:
                print("Congrats!\n")
                print(f'{len(self.results)}/{self.n_guesses}')
                for ur in self.unicode_results:
                    print(ur)

        elif self.done:
            if self.verbose:
                print('TOO BAD! SO SAD!')
                print(f'X/{self.n_guesses}')
                for ur in self.unicode_results:
                    print(ur)

        return result
    
    def _result(self, guess: str) -> str:
        result = list(guess) # use copy of the guess as template for building result
        filtered_word = list(self.word) # use copy of Wordle word to filter correct guesses out
        not_green_i = []

        # evaluate green choices & filter out greens
        for i, guess_letter in enumerate(guess):
            if guess_letter == self.word[i]:
                result[i] = 'G'
                filtered_word[i] = '_'
            else:
                not_green_i.append(i)
        
        # next evaluate yellow or black. filter out yellow as found left to right.
        for i in not_green_i:
            if guess[i] in filtered_word:
                result[i] = 'Y'
                y_filter = [j for j in range(len(self.word)) if guess[i] == filtered_word[j]][0]
                filtered_word[y_filter] = '_'
            else:
                result[i] = 'K'

        return "".join(result)


def main() -> None:

    print('W'*N_CHAR)
    print('Wordle'.center(N_CHAR))
    print("W"*N_CHAR)
    print("\n")

    print('Loading all English words...', end='')
    wordbank = pd.read_csv(ALPHA, header=None, keep_default_na=False)
    wordbank.columns = ['word']
    print('Done.\n')

    print('+' * N_CHAR)
    word = getpass('Enter a word: ')
    word = word.lower()
    
    # screen for valid guesses
    not_valid_word = ((wordbank.word == word.lower()).sum() < 1)
    while not_valid_word:
        print(f'"{word}" is not a word.')
        word = getpass(f'Enter a word: ')
        word = word.lower()
        not_valid_word = ((wordbank.word == word).sum() < 1)
    n_letters = len(word)
    print('+' * N_CHAR)
    print("\n")

    # filtering wordbank down
    wordbank = wordbank[wordbank.word.str.len().astype(int) == n_letters].copy()
    
    Wordle = WordleSimulator(word)
    while not Wordle.done:
        print('*' * N_CHAR)
        guess = input(f'Guess a {n_letters} letter word: ')
        guess = guess.lower()
        
        # screen for valid guesses
        not_valid_guess = ((wordbank.word == guess.lower()).sum() < 1)
        while not_valid_guess:
            n_guess = len(guess)
            if n_guess != n_letters:
                print(f'Must guess {n_letters}-letter word. Your word was {n_guess} letters.')
            else:
                print(f'"{guess}" is not a word.')
            guess = input(f'Guess a {n_letters} letter word: ')
            guess = guess.lower()
            not_valid_guess = ((wordbank.word == guess).sum() < 1)
        
        # compute guess
        Wordle.guess(guess)


if __name__ == '__main__':
    main()