This tool lists certain git attributes for code projects in the current directly.

It's output to standard out is tabular, comma-separated, with heading columns Name, Repo, Origin.

For each immediate child of the current directory that is a directory, the tool outputs a row where

- Name is the name of the directory
- Repo is "True" if the directory is a git repo, "False" otherwise
- Origin is the URI of the origin of the git repo, if one exists, single space otherwise.
