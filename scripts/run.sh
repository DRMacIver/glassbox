#!/bin/bash

set -e
set -x

eval "$(pyenv init -)"
pyenv shell 3.4.3
export PATH="$HOME/snakepit:$HOME/.pyenv/bin:$PATH"
tox -- $TOX_FLAGS
