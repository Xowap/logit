logit
=====

Simple python script to help turning Git logs into time sheets.

It will compute the duration of each task based on the time between two
commits. However if commits are more than 3h apart (or another value, it's
configurable) then that duration will be used instead.

Due to the method of computation, it's useful to run it on all the repositories
that you worked on during the time period you are seeking to investigate.
Indeed, the more traces of your activity you have, the more precise the
durations will be.

The optional parameter `--title-exp` allows you to transform commit messages
into a more usable title. By example, you can look for the issue tracker
reference.

Example:

```bash
bin/logit.py \
    --author 'Rémy Sanchez' \
    --title-exp '((([a-zA-Z\-_]+/)*[a-zA-Z\-_]+)(#[0-9]+))' \
    --output /tmp/time_sheet.csv \
    ~/dev/proj1 \
    ~/dev/proj2 \
    ~/dev/proj3
```

Requires Python 3.5+ and git. Dependencies are listed in `requirement.txt`.
