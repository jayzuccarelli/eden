# Eden: Bill of Materials

Every part for one Eden bucket: what it is, the exact product, where it came from,
and whether it's bought. Picks were made to a "buy-once-right, sensible-not-cheap"
bar, **don't re-research these.** Build steps for each part live in [BUILD.md](BUILD.md).

Status: ✅ bought · 🏠 already owned · ⏳ deferred/optional

## Controller (the brain)

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| XIAO ESP32-S3 Sense | Runs the reflex firmware; reads sensors, drives switches; has camera + mic | Seeed XIAO ESP32-S3 Sense | Amazon `B0C69FFVHH` | 🏠 |

## Sensing

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| pH probe | 24/7-immersion pH probe + signal-conditioning board (includes the board) | DFRobot Gravity **Industrial pH Sensor PRO** SEN0169-V2 (~$63) | **Arrow** (not Amazon, DigiKey was 9wk backordered; Arrow sells to individuals, itemizes the ~35% China-import tariff) | ✅ |
| ADC | 16-bit analog→I²C translator that lets the XIAO read the pH board's 0–3V output | ADS1115 16-bit, 2-pack (**not** the 12-bit ADS1015) | Amazon | ✅ |
| Water temp | Water-temperature probe; adapter has the 4.7k pull-up built in | BOJACK DS18B20 kit | Amazon `B09NVWNGLQ` | ✅ |

## Actuation (the muscles)

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| MOSFET drivers | Low-side switches: XIAO turns 12V loads on/off (pump on/off, light PWM) | HiLetgo IRF520 5-pack, use 2, 3 spare (1 reserved for a v2 nutrient pump) | Amazon `B01I1J14MO` | ✅ |
| Dosing pump | Pump #1, doses pH-Down into the bucket | Kamoer NKP 12V peristaltic | Amazon `B07GWJ78FN` | ✅ |
| Grow light | Plant light; XIAO PWM-dims it via MOSFET. White (not blurple) for a desk showpiece | VST 12V 4000K CRI90 white LED strip, 8ft | Amazon `B09TDND2W4` | ✅ |

## Power & wiring

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| 12V supply | Powers the muscles (pump + light); the XIAO runs separately off USB | ALITOVE 12V 5A brick | Amazon | ✅ |
| Barrel adapter | Brick plug → two screw terminals to feed the MOSFET boards | QLXHBOT 5.5×2.1mm female barrel connectors | Amazon | ✅ |
| Breadboard | The +3.3V / GND backbone everything plugs into | Elegoo breadboard kit | Amazon | ✅ |
| Hookup wire | Jumpers / load wiring | 22 AWG silicone wire | Amazon | ✅ |
| Heat shrink | Insulate the soldered LED-strip leads | Ginsco assortment | Amazon | ✅ |
| Iron + solder | Solder XIAO/ADS headers and the LED-strip leads | Pinecil + solder | 🏠 | 🏠 |

## Chemistry & consumables

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| pH-Down | What the dosing pump squirts to lower pH | General Hydroponics pH Control Kit / pH-Down | Amazon `B000BNKWZY` | ✅ |
| Nutrients | Single-part nutrient = simpler dosing | GH MaxiGro | Amazon `B00NQANQAC` | ✅ |
| Calibration buffers | 4.00 + 7.00 reference liquids to calibrate the probe | Apera AI1113 | Amazon `B0CDHM6QBC` | ✅ |
| Seed-start | Germinate in plugs, transplant rooted plug into the net pot (never sow in bucket water) | GH Rapid Rooter Tray + 50 plugs | Amazon `B000I63VSE` | ✅ |

## Grow vessel

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| DWC bucket kit | Bucket, 8" net-pot basket, air pump + stone, clay pebbles, water-level gauge | VIVOSUN 1-bucket DWC | Amazon `B09JSBJXRF` | ✅ |

## Seeds

| Part | Role | Product | Source | Status |
|---|---|---|---|---|
| Basil | The plant. True Ligurian/Tigullio Genovese cultivar (for *pesto di Prà*) | Basil "Italiano Classico Tigullio" cat# 13-7 | **growitalian.com** (Seeds from Italy, ships Kansas ~1wk) | ✅ |

## Deferred / optional

| Part | Why you might add it | Product | Status |
|---|---|---|---|
| Quiet air pump | Buy-once upgrade over the kit's hummy pump (matters for a 24/7 Zoom-visible desk), stays dumb/always-on, **never** agent-controlled | EHEIM Air Pump 100 `B0018CDWLS` | ⏳ |
| EC/TDS pen | Manual nutrient-strength spot-checks; full EC automation is v2 | HM Digital COM-100 `B0045LQFTK` | ⏳ |
| Solderless strip connectors | Only if you skip soldering the LED strip | ~$6 generic | ⏳ |

---

**Vendor notes:** Arrow.com sells to individuals, ships fast in the US, and
itemizes import tariffs (Amazon hides them in the sticker price). growitalian.com /
"Seeds from Italy" ships from Kansas, ~1 week.

**Tool limitation:** Amazon blocks automated price/stock lookups, so this lists
ASINs, confirm live price/availability on-screen.
