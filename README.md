# pyAbacus

pyAbacus was built to simplify the usage of Tausand Abacus family of coincidence counters, providing a library aimed to interface these devices using Python coding.

Written in Python3, pyAbacus relies on the following modules:
- pyserial


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

### Building docs
Go to the `docs` folder and run
```
make <command>
```
Where `<command>` is one of the following:
- `latexpdf`
- `html`

To run the `latexpdf` command you will need a working installation of Latex.
