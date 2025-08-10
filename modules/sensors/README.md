# Sensor Modules

## Nitrate (NO₃⁻) Probe

* **Model**: Atlas Scientific EZO-NO3.
* **Calibration**:
  1. Place probe in dry air and issue `Cal,dry` command.
  2. Submerge in a 100 mg/L standard and issue `Cal,100`.
  3. Rinse and return to sample.

## Oxidation-Reduction Potential (ORP) Probe

* **Model**: Atlas Scientific EZO-ORP.
* **Calibration**:
  1. Use ORP calibration solution (e.g., 225 mV).
  2. Insert probe and wait for reading to stabilize.
  3. Issue `Cal,225` command.

Both probes communicate over I²C and are polled using the functions in
`les/modules/sensors/nutrients.py`.
