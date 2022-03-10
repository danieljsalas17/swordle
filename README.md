# wordle-solver
A `pip` installable Wordle game, solver, and strategy assessment.

## Description
Simulate a wordle game, and then try solving it with a few different programmable strategies. First, we will try solving in "hard mode", where characters cannot be guessed again if already noted as not in the word, green characters must remain in place in future guesses, and yellow characters must be in future guesses. These rules forbid guessing disjoint sets of characters in a subsequent guess if a prior guess has correctly guessed a character, and forbids moving a correctly placed letter.

### Data

More information in [Data](data/) section.

### Solvers

Specific algorithms described in [Source Code](src/).

