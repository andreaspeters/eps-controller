# EPS-103 Controller for GPredict

With this small program, it is possible to control the EPS-103
rotor controller with GPredict. The project is based on an existing script by
Gabe Emerson (known from the YouTube channel Saveitforparts).

[![](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=ZDB5ZSNJNK9XQ)

## How to use

To install the software, simply clone the repository and install the required
Python dependencies:

```bash
git clone https://github.com/andreaspeters/eps-controller
cd eps-controller
pip install -r requirements.txt
```

## Configuration

Next, edit the file src/rotor.py and adjust the serial_port variable to match
the USB or COM port your EPS-103 controller is connected to.

By default, the controller communicates at 1200 baud. If your configuration
differs, you can change the baud rate at the bottom of the same file.

## Running the Program

To start the server, run:

```bash
python src/rotor.py
Listening on 0.0.0.0:4533
```

