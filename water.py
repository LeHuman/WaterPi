import os
import subprocess
import time
import argparse
import signal
import pathlib
import builtins

import RPi.GPIO as GPIO
from termcolor import colored, cprint

os.chdir(pathlib.Path(__file__).resolve().parent)

original_print = builtins.print
PRINT_PREFIX = colored("[WaterPi] ", 'cyan', attrs=['bold'])


def print_l(*args, **kwargs):
    """print override function"""
    original_print(PRINT_PREFIX, *args, **kwargs)


def eprint(text: str):
    """Print an error string"""
    cprint(text, 'red', attrs=['bold'])


def dprint(text: str):
    """Print a debug string"""
    cprint(text, attrs=['dark'])


builtins.print = print_l


class Device:
    """Struct class for a controlled device"""

    def __init__(self, name: str, pin1: int, pin2: int):
        self.name = name
        self.pin1 = pin1
        self.pin2 = pin2


# Initialize the devices
DEVICES = {
    "pump": Device("Pump", 17, 27),
    "heater": Device("Heater", 23, 24),
}


def read_gpio_state(pin: int) -> bool:
    """Reads the state of a GPIO pin using the `pinctrl get` command."""
    try:
        result = subprocess.run(
            ["pinctrl", "get", f"{pin}"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.lower()
        return ("none" in result) or ("hi" in result)
    except subprocess.CalledProcessError as e:
        eprint(f"Error reading state for GPIO {pin}: {e}")
        return True


# Setup GPIO with the detected initial state
GPIO.setmode(GPIO.BCM)
max_name_len = max([len(x) for x in DEVICES.keys()])
for device in DEVICES.values():
    pin1_state = GPIO.HIGH if read_gpio_state(device.pin1) else GPIO.LOW
    pin2_state = GPIO.HIGH if read_gpio_state(device.pin2) else GPIO.LOW

    off = colored('Off', 'red', attrs=["bold", "dark"])
    on = colored('On', 'green', attrs=["bold"])

    pin1_str = off if pin1_state == GPIO.HIGH else on
    pin2_str = off if pin2_state == GPIO.HIGH else on

    print(
        f"{colored(device.name.ljust(max_name_len), attrs=['bold'] )} {device.pin1}: {pin1_str} {device.pin2}: {pin2_str}")

    GPIO.setup(device.pin1, GPIO.OUT, initial=pin1_state)
    GPIO.setup(device.pin2, GPIO.OUT, initial=pin2_state)


def enable_device(device_name: str):
    """Enables the specified device by toggling its GPIO pins."""
    try:
        device = DEVICES[device_name]

        GPIO.output(device.pin1, GPIO.LOW)
        time.sleep(0.25)  # ~250ms delay
        GPIO.output(device.pin2, GPIO.LOW)

    except Exception as e:
        eprint(f"Error enabling {device_name}: {e}")
        fallback_disable_all()
        raise


def disable_device(device_name: str):
    """Disables the specified device by toggling its GPIO pins."""
    try:
        device = DEVICES[device_name]

        GPIO.output(device.pin2, GPIO.HIGH)
        time.sleep(0.10)  # ~100ms delay
        GPIO.output(device.pin1, GPIO.HIGH)

    except Exception as e:
        eprint(f"Error disabling {device_name}: {e}")
        fallback_disable_all()
        raise


def enable_device_for(device_name: str, duration_ms: int):
    """Enables a device for a specified duration in milliseconds."""
    try:
        enable_device(device_name)
        time.sleep(duration_ms / 1000.0)  # Convert ms to seconds
    except Exception as e:
        eprint(f"Error in enable_device_for: {e}")
        fallback_disable_all()
        raise
    finally:
        try:
            disable_device(device_name)
        except Exception as cleanup_error:
            eprint(f"Error during cleanup of {device_name}: {cleanup_error}")
            fallback_disable_all()


def fallback_disable_all(*args):
    """Disables all devices immediately without stepped behavior."""
    cprint("Fallback: Disabling all devices", 'red', attrs=['bold', 'underline'])
    for device in DEVICES.values():
        GPIO.setup(device.pin1, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(device.pin2, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.output(device.pin1, GPIO.HIGH)
        GPIO.output(device.pin2, GPIO.HIGH)
    exit(1)


def notify_watchdog(pipe_path):
    """Send a graceful exit signal to the external watchdog via the named pipe."""
    if os.path.exists(pipe_path):
        with open(pipe_path, 'w', encoding='utf-8') as pipe:
            pipe.write("FINISH\n")
    else:
        eprint("Pipe not found; external watchdog might not be running.")
        fallback_disable_all()


def start_watchdog(timeout_ms: int) -> str:
    """Start the external watchdog and create relevant pipe"""
    pipe_path = f"/tmp/external_script_pipe_{int(time.time())}"
    dprint(f"Using watchdog pipe {pipe_path}")

    # Ensure the pipe doesn't exist already
    if os.path.exists(pipe_path):
        os.remove(pipe_path)

    # Always have at least three seconds of grace
    timeout = int(((timeout_ms * 1.25) / 1000) + 3)

    # Start the external watchdog
    script_path = "./py_watchdog.sh"
    command = ["bash", script_path, pipe_path, str(timeout)]
    _pid = os.spawnvpe(os.P_NOWAIT, command[0], command, os.environ)

    # Give a second to start script
    watch = time.time()
    while not os.path.exists(pipe_path):
        if (time.time() - watch > timeout):
            eprint("Failed to create watchdog in time")
            fallback_disable_all()

    cprint(f"Watchdog created for {timeout}s", 'yellow')

    return pipe_path


# List of fatal signals to catch
fatal_signals = [
    signal.SIGINT,   # Interrupt signal
    signal.SIGTERM,  # Termination signal
    signal.SIGABRT,  # Abort signal
    signal.SIGHUP,   # Hangup signal
]

# Register signal handlers
for sig in fatal_signals:
    signal.signal(sig, fallback_disable_all)


def main():
    """Command-line interface for remotely watering a plant"""
    parser = argparse.ArgumentParser(description="GPIO Device Control")
    parser.add_argument("command", choices=["status", "enable", "disable", "kill",
                        "enable_for"], help="Action to perform on a device")
    parser.add_argument("device", nargs="?", choices=DEVICES.keys(), help="The name of the device to control")
    parser.add_argument("duration", nargs="?", type=int, help="Duration in milliseconds for 'enable_for' command")

    args = parser.parse_args()
    errored = False

    try:
        if args.command == "kill":
            cprint("Using fallback disable function to kill all", 'red')
            errored = True
            fallback_disable_all()
        elif args.command == "status":
            pass
        else:
            if os.path.exists("./fail"):
                eprint("Fail flag detected, did you restore power?")
                exit(1)

            if args.device is None:
                raise ValueError("Device argument is required for commands\n choices:\n  " +
                                 "\n  ".join(DEVICES.keys()))
            elif args.command == "enable":
                pipe = start_watchdog(500)
                enable_device(args.device)
                notify_watchdog(pipe)
            elif args.command == "disable":
                pipe = start_watchdog(500)
                disable_device(args.device)
                notify_watchdog(pipe)
            elif args.command == "enable_for":
                if args.duration is None:
                    raise ValueError("Duration argument is required for 'enable_for' command")
                pipe = start_watchdog(args.duration)
                enable_device_for(args.device, args.duration)
                notify_watchdog(pipe)
    except Exception as e:
        eprint(f"Error in main: {e}")
        fallback_disable_all()
        errored = True
    finally:
        if args.command == "enable_for":
            try:
                disable_device(args.device)
            except Exception as cleanup_error:
                eprint(f"Error during final cleanup of {args.device}: {cleanup_error}")
                fallback_disable_all()
        elif not errored:
            dprint("Leaving devices in their current state.")
    cprint("Done! 💧", 'blue', attrs=['bold'])


if __name__ == "__main__":
    main()
