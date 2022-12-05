# ead-html-validator

## About ##

ead-html-validator is a command line tool that validates a set
of Finding Aids HTML files generated by Hugo.  The HTML is
deemed valid if the content of an ArchiveSpace EAD appears
within the HTML files. Please reference JIRA ticket FADESIGN-230
for more information.

## Requirements ##

ead-html-validator requires Python >= 3.7 and depends on the
following modules:

- beautifulsoup4
- pycountry
- python-dateutil
- requests
- lxml
- thefuzz

## Installation

Checkout validator repository on github:

    $ cd ~
    $ git clone https://github.com/rrasch/ead-html-validator.git

Set up virtual environment:

    $ mkdir ~/venv
    $ cd ~/venv
    $ python3 -m venv ead-html-validator
    $ source ead-html-validator/bin/activate
    $ pip3 install -r ~/ead-html-validator/requirements.txt

Test out the script:

    $ cd ~/ead-html-validator
    $ ./ead-html-validator.py

To exit the virtual enviroment:

    $ deactivate

## Usage ##

The tools takes in two arguments:

- the path to an EAD xml file
- the path to a directory containing HTML files

The command line looks like the following

    ead-html-validator <ead_xml_file> <finding_aids_html_dir>

## Debugging

Add the -d switch for debugging output

