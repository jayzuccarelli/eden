# Building your own Eden

Eden is a single DWC (deep water culture) bucket growing one basil plant, tended
by a Claude "Gardener" agent through Home Assistant. This is the parts list and
wiring to build the physical half.

**The compute is free.** Any always-on box running Home Assistant plus a Claude
API key runs the whole software stack, you don't buy a server for this. What you
buy is the grow system, the sensors, the actuators and their drivers, one
microcontroller, and consumables. Rough all-in cost is **~$250–350** depending on
what you already own and which optional upgrades you take.

> Product links are Amazon ASINs / vendor SKUs that were current at the time of
> writing, prices and availability drift, so confirm before you buy. Anything
> from China (the pH probe especially) may carry an import tariff that a US
> vendor itemizes and Amazon hides in the sticker price.

## Bill of materials

### Grow system
| Part | Where | Notes |
|---|---|---|
| DWC bucket kit, **VIVOSUN 1-bucket** | Amazon `B09JSBJXRF` | Bucket, 8" net basket, air pump + stone, clay pebbles, water-level gauge. The kit is the fastest way to a complete bucket. |
| *(optional)* Quieter air pump, **EHEIM Air Pump 100** | Amazon `B0018CDWLS` | Buy-once upgrade over the kit's hummy pump. Worth it if the garden sits on a desk / in view on calls. |

### Controller (reflex tier)
| Part | Where | Notes |
|---|---|---|
| **Seeed XIAO ESP32-S3 (Sense)** | Amazon `B0C69FFVHH` | Runs the ESPHome reflex firmware in `esphome/`. The Sense variant adds a camera + mic you don't strictly need for v1 but are nice for a plant-cam later. |

### Sensors
| Part | Where | Notes |
|---|---|---|
| pH probe, **DFRobot Gravity Industrial pH Sensor PRO** `SEN0169-V2` | Arrow (`arrow.com`) | 24/7 immersion-rated, most consumer probes are not. Kit includes the signal-conditioning board that outputs 0–3 V analog. (DigiKey was backordered ~9 weeks; Arrow sells to individuals.) |
| ADC, **ADS1115** 16-bit, I²C | Amazon (2-pack) | Reads the pH board's analog out. 16-bit matters, avoid the 12-bit ADS1015. |
| Water temp, **BOJACK DS18B20** waterproof kit | Amazon `B09NVWNGLQ` | The kit's adapter has the 4.7 kΩ 1-Wire pull-up built in. |
| *(optional)* EC/TDS pen, **HM Digital COM-100** | Amazon `B0045LQFTK` | Manual nutrient-strength spot checks. Full EC automation is a v2 concern. |

### Actuators + drivers
| Part | Where | Notes |
|---|---|---|
| Dosing pump, **Kamoer NKP 12V** peristaltic | Amazon `B07GWJ78FN` | Doses pH-Down. Peristaltic = precise small volumes, no cross-contamination. |
| MOSFETs, **HiLetgo IRF520** 5-pack | Amazon `B01I1J14MO` | Low-side switching for the pump (on/off) and light (PWM). You use 2; keep spares for a v2 nutrient pump. |
| Grow light, **VST 12V 4000K CRI90** white LED strip, 8 ft | Amazon `B09TDND2W4` | Bare strip; the XIAO PWM-dims it through a MOSFET. White (not "blurple") for a garden you actually want to look at. |
| **12V / 2A power brick** | from home or Amazon | Powers the pump and light rail. Reuse a spare router/HDD/LED adapter if you have one. |

### Chemistry + consumables
| Part | Where | Notes |
|---|---|---|
| pH-Down, **General Hydroponics pH Control Kit** | Amazon `B000BNKWZY` | The pump doses from this. Kit also has pH-Up + test drops. |
| Calibration buffer, **Apera AI1113** 4.00 + 7.00 | Amazon `B0CDHM6QBC` | Two-point calibration for the probe. Do this before trusting any reading. |
| Nutrients, **GH MaxiGro** | Amazon `B00NQANQAC` | Single-part powder = simplest dosing for one bucket. |
| Rockwool, **Grodan A-OK 1.5"**, 49-cube sheet | Amazon `B0742KTHNQ` | Soilless germination medium. Never use dirt, soil fouls the DWC water and air stone. |
| Seeds, Basil **"Italiano Classico Tigullio"** (cat# 13-7) | `growitalian.com` (Seeds from Italy) | The authentic Ligurian Genovese cultivar. Generic "Genovese" packets work too; this is the real one for pesto. |

### From home / already owned
12V brick (if you have a spare), jumper wires, a soldering iron + solder (for the
LED strip, or buy solderless strip connectors, ~$6), a machine running Home
Assistant, and a Claude API key.

## Wiring: XIAO ESP32-S3

These are the **verified pin assignments** baked into `esphome/eden-zone.yaml`.
Match them exactly or change both the wiring and the firmware substitutions.

| Signal | XIAO pin | Connects to |
|---|---|---|
| I²C SDA | `GPIO5` (D4) | ADS1115 SDA |
| I²C SCL | `GPIO6` (D5) | ADS1115 SCL |
| pH analog in | *(none)* | pH signal board out → **ADS1115 A0** |
| Water temp (1-Wire) | `GPIO3` (D2) | DS18B20 data |
| pH-Down pump | `GPIO1` (D0) | IRF520 gate → pump `−`, pump `+` to 12V |
| Grow light (PWM) | `GPIO2` (D1) | IRF520 gate → LED strip `−`, strip `+` to 12V |
| **Air pump** | *(none)* | **Wall power, always on, NOT wired to the MCU** |

Notes:
- ADS1115 sits at I²C address `0x48`, pH on channel A0, gain 4.096 (matches the
  probe's 0–3 V range).
- MOSFETs are low-side switches: **source → GND, drain → load `−`, gate → GPIO.**
  Tie the XIAO ground, the 12V-brick ground, and the MOSFET sources together.
- The XIAO is USB-powered; the 12V brick powers only the pump and light rail.

## Safety: the reflex tier, in firmware (not the agent)

The whole point of the two-tier design is that safety lives in firmware and holds
even if the Gardener agent is offline or misbehaving:

- **The air pump is life support.** It runs on dumb, always-on wall power and is
  **never** wired to the controller or exposed as an agent actuator. The firmware
  only *reads* an `air_pump_ok` state for alerting, it can't turn the pump off.
- **The pH dose has a hard 2-second auto-off** (`dose_cap_s` in the firmware). The
  agent calls `turn_on`; the firmware turns it off. The agent physically cannot
  run a dose long enough to overdose the bucket.
- **The light runs a 14-hour photoperiod** on its own schedule, independent of the
  agent.

## Flash the firmware

1. Install [ESPHome](https://esphome.io/).
2. Create `esphome/secrets.yaml` (gitignored) with your WiFi:
   ```yaml
   wifi_ssid: "your-ssid"
   wifi_password: "your-password"
   ```
3. Flash the zone-1 node:
   ```
   esphome run esphome/eden-z1.yaml
   ```

Entities then appear in Home Assistant as `sensor.eden_z1_ph`,
`sensor.eden_z1_water_temp`, `binary_sensor.eden_z1_air_pump_ok`,
`switch.eden_z1_ph_down_dose`, and `light.eden_z1_grow_light`: exactly the
entity IDs `instance/zones.yaml` maps each role to.

A **second bucket** is a second node: `cp eden-z1.yaml eden-z2.yaml`, change
`zone: z2`, re-flash. Every entity is prefixed `eden_<zone>_<role>`, so zones can
never collide and Home Assistant history is never re-keyed.

## Germinate

1. Soak the Grodan cubes ~1 hour in pH ~5.5 water (a few drops of pH-Down + the
   GH test drops to check).
2. Seed the cubes and germinate **soilless**: never in dirt, which fouls the DWC
   water and air stone. A disposable lasagna pan with a poked-hole lid and ~¼" of
   water makes a fine humidity dome.
3. Once the cube has roots, transplant the **whole cube** into the net basket,
   roots toward the water. Never sow directly into the bucket.

Then calibrate the pH probe against the 4.00 / 7.00 buffers, fill the bucket with
nutrient solution, and let the Gardener take over.
