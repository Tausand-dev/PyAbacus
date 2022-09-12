# pyAbacus

pyAbacus is built to simplify the usage of Tausand Abacus family of coincidence counters, providing a library aimed to interface these devices using Python coding.

Written in Python3, pyAbacus relies on the following modules:
- pyserial

Library version:       1.2.0<br/>
Original release date: 12/28/2017 (mm/dd/yyyy)<br/>
Current revision date: 09/12/2022<br/>
Supported models:      AB1002, AB1004, AB1502, AB1504, AB2502, AB2504.

## About Tausand Abacus AB1000

This is a family of coincidence counters, ideal to measure temporal correlations in particle detection and quantum optics experiments.

To learn more about them, visit our website www.tausand.com

To obtain a Tausand's Abacus coincidence counter, visit our [online shop](http://www.tausand.com/shop) or contact us at sales@tausand.com

## Installation
`pyAbacus` can be installed using `pip` as: 
```
pip install pyAbacus
```

Or from GitHub
```
pip install git+https://github.com/Tausand-dev/PyAbacus.git
```

## Examples and documentation
To learn how to use pyAbacus, take a look at the `examples` folder and run the scripts after you've installed `pyAbacus`. For more details on how to run this library, read `PyAbacus_Documentation.pdf` or navigate the HTML version located at `docs/build/html/index.html`.

## For developers

Clone the GitHub repository and then follow the next steps:

### Creating a virtual environment
Run the following code to create a virtual environment called `.venv`
```
python -m venv .venv
```

#### Activate
- On Unix systems:
```
source .venv/bin/activate
```
- On Windows:
```
.venv\Scripts\activate
```

#### Deactivate
```
deactivate
```

### Installing packages
After the virtual environment has been activated, install required packages by using:
```
python -m pip install -r requirements.txt
```
This will allow you to build the documentation using Sphinx.

### Editing version number
When a new version is created, the new numbering should be updated in the following files:
- docs/source/conf.py
- pyAbacus/\_\_init__.py 
- setup.cfg

### Building docs
Go to the `docs` folder and run
```
make <command>
```
Where `<command>` is one of the following:
- `latexpdf`
- `html`

To run the `latexpdf` command you will need a working installation of Latex.
