import json
import utils


def update_param_file(r_footprint):
    """Write a student-friendly simulation configuration."""
    config = {
        "r_footprint": r_footprint,
        "h_satellite": 600e3,
        "center_frequency": 30e9,
        "bandwidth_Hz": 25e6,
        # Reduced from 32x32 so the model runs on a normal laptop.
        "n_antenna_x": 8,
        "n_antenna_y": 8,
        "antenna_gain_dB": 60.5,
        "rician_k": 10,
        "transmit_power_W": 63,
        "n_beams_x": 5,
        "n_beams_y": 4,
        "n_beams": 19,
        "noise_figure_dB": 7,
        "t_frame": 10e-3,
        "r_earth": 6371e3,
        "v_satellite": 7.56e3,
        "SPEED_OF_LIGHT": 299792458,
        "BOLTZMANN_CONSTANT": 1.3806485e-23,
        "temperature_K": 300,
        "latitude_center": 35.67619190,
        "longitude_center": 139.65031060,
        "D": 0,
        "p": 1,
    }
    with open('params.json', 'w') as f:
        json.dump(config, f, indent=2)


def get_antenna_spacing():
    config = read_params()
    return config["SPEED_OF_LIGHT"] / config["center_frequency"] / 2


def get_noise_power():
    config = read_params()
    return (config["BOLTZMANN_CONSTANT"] * config["temperature_K"] *
            config["bandwidth_Hz"] * utils.from_dB(config["noise_figure_dB"]))


def read_params():
    with open('params.json', 'r') as f:
        return json.load(f)
