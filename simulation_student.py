"""Student-friendly multi-beam LEO simulation.

Runs the same basic channel/beam/SNR/SINR model as the reference code,
but with a reduced computational load and many elevation angles.
"""
import json
from pathlib import Path

import numpy as np

import channel
import networkGeometry
import params
import utils

RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True)

# 18 angles: 5, 10, ..., 90 degrees.
# These are measured at the centre of the satellite footprint.
ELEVATION_ANGLES_DEG = np.arange(5, 91, 5)

# Student-friendly workload.
RICIAN_USERS = 300
Rician_FOOTPRINTS_M = np.array([100e3])  # keep one representative footprint
MACRO_GRID_SPACING_M = 20e3               # NOT number of users; grid spacing


def get_frame_for_elevation(sat_pos, elevation_deg):
    """Return the satellite frame closest to the requested centre elevation."""
    elevations = utils.get_elevation_angle_from_center(sat_pos[0], sat_pos[2]) / np.pi * 180
    # Avoid tiny floating-point overshoot around 90 degrees.
    elevations = np.clip(elevations, 0.0, 180.0)
    idx = int(np.argmin(np.abs(elevations - elevation_deg)))
    return idx


def calculate_simulation_result(channel_, n_user, beam_index, beam_gain, ant_gain_db):
    rec_power = np.abs(channel_) ** 2
    desired_power = rec_power[np.arange(n_user), beam_index]
    receive_power = np.sum(rec_power[:, :], axis=1)
    interference_power = receive_power - desired_power
    noise = params.get_noise_power()
    sinr = utils.to_dB(desired_power / (interference_power + noise))
    snr = utils.to_dB(desired_power / noise)
    center_beam_gain_dB = utils.to_dB(np.abs(beam_gain[np.arange(n_user), 9]) ** 2) + ant_gain_db
    return sinr, snr, center_beam_gain_dB


def run_rician():
    """Run Rician simulations at many elevation angles."""
    result_file_prefix = "macro_with_Rician"
    params.update_param_file(Rician_FOOTPRINTS_M[0])
    config = params.read_params()
    ant_gain_dB = config["antenna_gain_dB"]

    sat_pos = networkGeometry.get_satellite_pos()
    # Make the zenith position exact, matching the reference model.
    zenith_idx = int(np.argmin(np.abs(utils.get_elevation_angle_from_center(sat_pos[0], sat_pos[2]) / np.pi * 180 - 90)))
    sat_pos[:, zenith_idx] = np.array([0, 0, config["h_satellite"]])

    beam_centers = networkGeometry.hex_grid_centers_two_rings()
    user_pos = networkGeometry.get_user_position(RICIAN_USERS)
    n_user = user_pos.shape[1]

    print(f"Student Rician simulation: {n_user} users, {config['n_antenna_x']}x{config['n_antenna_y']} antennas/beam")
    print(f"Elevation angles: {list(ELEVATION_ANGLES_DEG)} degrees")

    for elevation_deg in ELEVATION_ANGLES_DEG:
        i_frame = get_frame_for_elevation(sat_pos, elevation_deg)
        i_sat_pos = sat_pos[:, i_frame]
        actual_elevation = float(utils.get_elevation_angle_from_center(i_sat_pos[0], i_sat_pos[2]) / np.pi * 180)
        print(f"  Rician: requested {elevation_deg}°, actual {actual_elevation:.3f}°")

        loss_dB = channel.path_loss(user_pos, i_sat_pos)
        precoder_analog = channel.fixed_beam_steering(i_sat_pos, beam_centers)
        micro_channel, macro_channel, beam_gain = channel.get_effective_channel(
            loss_dB, precoder_analog, i_sat_pos, user_pos, n_user, i_frame
        )
        fading = np.abs(macro_channel) ** 2
        _, beam_index = np.where(np.transpose(np.transpose(fading) == fading.max(axis=1)))
        sinr, snr, bGain_dB = calculate_simulation_result(
            micro_channel, n_user, beam_index, beam_gain, ant_gain_dB
        )

        result = {
            "user_positions": user_pos.tolist(),
            "n_user": n_user,
            "satellite_position": i_sat_pos.tolist(),
            "snr": snr.tolist(),
            "sinr": sinr.tolist(),
            "beam_index": beam_index.tolist(),
            "center_beam_gain_dB": bGain_dB.tolist(),
            "beam_centers": beam_centers.tolist(),
            "r_footprint": float(Rician_FOOTPRINTS_M[0]),
            "elevation_angle": actual_elevation,
            "requested_elevation_angle": int(elevation_deg),
            "frame_index": i_frame,
        }
        filename = RESULT_DIR / f"{result_file_prefix}{int(elevation_deg)}deg_100km.json"
        with open(filename, "w") as f:
            json.dump(result, f)


def run_macro():
    """Run the deterministic macro simulation at the same elevation sweep."""
    r_footprint = 100e3
    params.update_param_file(r_footprint)
    config = params.read_params()
    ant_gain_dB = config["antenna_gain_dB"]

    sat_pos = networkGeometry.get_satellite_pos()
    zenith_idx = int(np.argmin(np.abs(utils.get_elevation_angle_from_center(sat_pos[0], sat_pos[2]) / np.pi * 180 - 90)))
    sat_pos[:, zenith_idx] = np.array([0, 0, config["h_satellite"]])

    # 20 km spacing gives a small, manageable macro grid.
    user_pos = networkGeometry.get_grid_positions(MACRO_GRID_SPACING_M)
    n_user = user_pos.shape[1]
    beam_centers = networkGeometry.hex_grid_centers_two_rings()
    print(f"Student macro simulation: {n_user} grid users, {MACRO_GRID_SPACING_M/1000:.0f} km spacing")

    for elevation_deg in ELEVATION_ANGLES_DEG:
        i_frame = get_frame_for_elevation(sat_pos, elevation_deg)
        i_sat_pos = sat_pos[:, i_frame]
        actual_elevation = float(utils.get_elevation_angle_from_center(i_sat_pos[0], i_sat_pos[2]) / np.pi * 180)
        print(f"  Macro: requested {elevation_deg}°, actual {actual_elevation:.3f}°")

        loss_dB = channel.path_loss(user_pos, i_sat_pos)
        precoder_analog = channel.fixed_beam_steering(i_sat_pos, beam_centers)
        _, macro_channel, beam_gain = channel.get_effective_channel(
            loss_dB, precoder_analog, i_sat_pos, user_pos, n_user, i_frame
        )
        fading = np.abs(macro_channel) ** 2
        _, beam_index = np.where(np.transpose(np.transpose(fading) == fading.max(axis=1)))
        sinr, snr, beam_gain_dB = calculate_simulation_result(
            macro_channel, n_user, beam_index, beam_gain, ant_gain_dB
        )

        result = {
            "user_positions": user_pos.tolist(),
            "n_user": n_user,
            "satellite_position": i_sat_pos.tolist(),
            "snr": snr.tolist(),
            "sinr": sinr.tolist(),
            "beam_index": beam_index.tolist(),
            "center_beam_gain_dB": beam_gain_dB.tolist(),
            "beam_centers": beam_centers.tolist(),
            "r_footprint": r_footprint,
            "elevation_angle": actual_elevation,
            "requested_elevation_angle": int(elevation_deg),
            "frame_index": i_frame,
        }
        filename = RESULT_DIR / f"macro_no_Rician{int(elevation_deg)}deg_100km.json"
        with open(filename, "w") as f:
            json.dump(result, f)


if __name__ == "__main__":
    run_rician()
    run_macro()
    print("\nStudent simulation completed successfully.")
    print("Results saved in the results/ folder.")
