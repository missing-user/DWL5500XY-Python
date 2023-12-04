# Project description
Python library and a small recording script for the Digipass DWL5500XY inclinometer. 

# Installation
> [!IMPORTANT]
> Both the libraries `serial` and `pyserial` can be imported as `import serial`. This module expects a `pyserial` installation, and will not work with the incorrect library!
```sh
git clone https://github.com/missing-user/DWL5500XY-Python/.git
cd DWL5500XY-Python
pip install -r requirements.txt
```


See the test.py for example code, most features are explored here.


> [!CAUTION]
> ***Calling the calibration function will overwrite the factory settings!***
>
> If you have purchased a new DWL5500XY sensor, i suggest to **NOT PERFORM A NEW CALIBRATION**! The sensor should be calibrated at the factory, and will most probably be better than what you can achieve, unless you really know what you're doing. You have been warned.
