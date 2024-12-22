<!-- PROJECT: WaterPi -->
<!-- TITLE: WaterPi -->
<!-- KEYWORDS: Controller, Raspberry Pi -->
<!-- LANGUAGES: Python, Bash -->

# WaterPi

[About](#about) - [Usage](#usage) - [Related](#related) - [License](#license)

## Status
<!-- STATUS -->
**`Prototype`**

## About
<!-- DESCRIPTION START -->
A set of scripts used to control an Amazon special 💲 relay board and a Kasa KP401 smart switch.
<!-- DESCRIPTION END -->

The physical setup will not be visualized here. But briefly put, the RPi has four `GPIO` to four `NO` active low relays for 120VAC power to a heater and water pump, this is `individual` power for each `device`. The KP401 controls upstream power to all relays for `main` power. There is also a USB camera with a builtin microphone connected to the RPi.

### Why

I did not have time to make anything fancier. My plant almost died when I left it for a week and I am leaving it for an even longer period of time. I bought all the parts and assembled / wrote everything in ~2 days before having to leave. I wanted more than one form of redundancy on power as this was all last minute.

Additionally, A lot of this is meant to be triggered on my phone through Termux, hence all the pre-defined scripts.

## Usage

> [!IMPORTANT]
> The following is meant to be run on a RaspberryPi 5 in this folder.

### Requirements

- [RaspberryPi 5](https://www.raspberrypi.com/products/raspberry-pi-5/)
  - Not tested on anything else
- [go2rtc](https://github.com/AlexxIT/go2rtc) >= 1.9.7
  - Download local binary with the following
    - `wget https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_arm64`
- [Python](https://www.python.org/) >= 3.11
  - Install dependencies by running the following

    ```sh
        sudo apt install -y python3-termcolor
        python -m venv env
        source env/bin/activate
        pip install -r requirements.txt
    ```

### Running

> [!NOTE]
> The KP401 can be controlled by anything on it's local network. Knowing an alternative to turn it off in case the RPi itself fails is a good idea to do. This repo does not cover that.

Direct python script functionality will not be covered, run `python3 water.py --help` for more info. Only relevant scripts are described here.

|script|function|
|------|--------|
| `./water.sh` | Enable water pump for how every many `ms` as defined in this bash script |
| `./heater_on.sh` | Enable heater |
| `./heater_off.sh` | Disable heater |
| `./kill.sh` | Cut all power including main |
| `./restore.sh` | Restore main power |
| `./status.sh` | Restore main power |
| `./monitor.sh &` | Turn on webcam stream (rec put in bg) |

> [!IMPORTANT]
> If anything goes wrong (or if you called `kill.sh`) you must call `restore.sh`, as main power will have been cut. If there is a file called `fail` in this directory, something went wrong and the main scripts will not run. Additionally, everything will (*should*) have been turned off.

## Related

- AlexxIT/[go2rtc](https://github.com/AlexxIT/go2rtc)
- python-kasa/[python-kasa](https://github.com/python-kasa/python-kasa)

## License

MIT
