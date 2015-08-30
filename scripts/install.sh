#!/bin/bash

# Special license: Take literally anything you want out of this file. I don't
# care. Consider it WTFPL licensed if you like.
# Basically there's a lot of suffering encoded here that I don't want you to
# have to go through and you should feel free to use this to avoid some of
# that suffering in advance.

set -e
set -x

# Somehow we occasionally get broken installs of pyenv, and pyenv-installer
# is not good at detecting and cleaning up from those. We use the existence
# of a pyenv executable as a proxy for whether pyenv is actually installed
# correctly, but only because that's the only error I've seen so far.
if [ ! -e "$HOME/.pyenv/bin/pyenv" ] ; then
  echo "pyenv does not exist"
  if [ -e "$HOME/.pyenv" ] ; then
    echo "Looks like a bad pyenv install. Deleting"
    rm -rf $HOME/.pyenv
  fi
fi

# Run the pyenv-installer script we've bundled.
# This is basically vendored from >https://github.com/yyuu/pyenv-installer
$(dirname $0)/pyenv-installer

# Now that pyenv is installed, run the commands it gives us to actually
# activate it.
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"


# pyenv update makes a lot of requests to github, which is not entirely
# reliable. As long as we got a working pyenv in the first place (above) we
# don't want to fail the build if pyenv can't update. Given that .pyenv is
# cached anyway, the version we have should probably be quite recent.
pyenv update || echo "Update failed to complete. Ignoring"

SNAKEPIT=$HOME/snakepit

rm -rf $SNAKEPIT
mkdir $SNAKEPIT

PYENVS=$HOME/.pyenv/versions

pyenv install -s 3.4.3
ln -s $PYENVS/3.4.3/bin/python $SNAKEPIT/python3.4
echo 3.4.3 > $HOME/.python-version
pyenv global 3.4.3
pyenv local 3.4.3

pyenv install -s 2.6.9
ln -s $PYENVS/2.6.9/bin/python $SNAKEPIT/python2.6
pyenv install -s 2.7.9
ln -s $PYENVS/2.7.9/bin/python $SNAKEPIT/python2.7
pyenv install -s 3.2.6
ln -s $PYENVS/3.2.6/bin/python $SNAKEPIT/python3.2
pyenv install -s 3.3.6
ln -s $PYENVS/3.3.6/bin/python $SNAKEPIT/python3.3
pyenv install -s pypy-2.6.0
ln -s $PYENVS/pypy-2.6.0/bin/pypy $SNAKEPIT/pypy
pip install --upgrade tox pip wheel
