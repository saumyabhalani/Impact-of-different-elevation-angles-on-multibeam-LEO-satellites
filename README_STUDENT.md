# Multi-Beam LEO Communication Simulation — Student Version

This folder is a computationally reduced version of the reference Multi-Beam LEO Communication Simulation Framework.

## What is preserved

The model still calculates:
- 19 satellite antenna beams
- antenna-array steering
- free-space path loss
- atmospheric attenuation
- Rician fading
- beam association
- co-channel interference
- SNR and SINR
- beam gain

## What is reduced

To make the simulation practical on a normal student laptop:
- Antenna array: **8 x 8 per beam** instead of 32 x 32
- Rician users: **300** instead of 100,000
- Macro grid spacing: **20 km** instead of 500 m
- Rician footprint: **100 km** for the main student run

## Elevation-angle sweep

Unlike the original reference run, which uses three main angles (90°, 55°, 25°), this student version evaluates **18 elevation angles**:

**5°, 10°, 15°, ..., 85°, 90°**

The program finds the satellite frame closest to each requested centre elevation.

## Run

Open this folder in VS Code and run:

```powershell
python simulation_student.py
```

When it finishes:

```powershell
python plotResults_student.py
```

Results are saved in `results/` and plots in `figures/`.

## Important

This is a reduced computational configuration. It is intended for learning, demonstrations, coursework, and testing the complete simulation workflow. Its numerical results should not be presented as an exact reproduction of the original paper's full-scale simulation.

The original reference files are preserved under `original_reference/`.
