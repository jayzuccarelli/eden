# Eden — Build Manual

The IKEA booklet for building one Eden bucket from a box of parts to a living,
self-tending plant. Read top to bottom. Each **Component** is a little sub-build:
you pick up some parts, wire them, test that one thing works, then **set it aside**
and move to the next. Nothing here needs water until the very end, so you can't
ruin anything while learning.

Two ideas that make the whole thing click:

1. **There are two power supplies.** A USB cable powers the *brain* (the little
   XIAO chip). A separate 12V wall brick powers the *muscles* (the pump and the
   light). They never mix — **except** they both connect to "ground." Think of
   ground as the common floor everything stands on. Brain on USB, muscles on 12V,
   and they shake hands at ground. If you forget the handshake, nothing works.

2. **The breadboard is the meeting point.** The breadboard has two long rails
   running down its edges — one we'll call the **+3.3V rail** (power for the small
   sensors) and one the **GND rail** (ground, the common floor). Almost everything
   plugs into these two rails. Get the rails right and the rest is just "this wire
   goes to that rail."

A breadboard, for reference: the long strips of holes along the two outer edges
are the **rails** (usually marked with a red `+` line and a blue `−` line). The
holes in the middle are where you plant chips and run jumper wires.

---

## Before you start — find your parts

Tip them all out and identify these. (Names in **bold** are what I'll call them
from here on.)

- **The brain** — a tiny board about the size of your thumbnail with a USB-C port
  on one short end. This is the *XIAO ESP32-S3*. It may come with two little black
  strips of pins not yet attached — keep those, we solder them on in Component A.
- **Two MOSFET boards** — small blue-ish boards, each with a silver metal block
  (that's the MOSFET), a row of **3 small pins** on one end labeled `SIG VCC GND`,
  and **two blue screw-terminal blocks** on the other end. You have 5; we use 2.
  These are the *switches* that let the tiny brain turn 12V things on and off.
- **The dosing pump** — a small motor (the *Kamoer*) with a clear tube threaded
  through it and two wires coming out. This squirts pH-Down liquid.
- **The grow light** — a flexible white LED strip on a reel.
- **The pH kit** — a glass probe (looks like a fat pen with a wire/BNC screw end)
  plus a small green/blue circuit board with a round silver screw connector on it.
  Plus two little bottles of liquid marked **4.00** and **7.00** (calibration).
- **The pH ADC** — a tiny board labeled *ADS1115* with `VDD GND SCL SDA A0 A1...`
  printed on it. This is the translator that lets the brain read the pH probe.
- **The thermometer** — a metal tube on a cable (the *DS18B20*) with a small
  adapter board and three wires (usually red, black, yellow).
- **The air pump + air stone** — a little box that hums and a porous stone on a
  hose. This is *dumb*: it plugs into the wall and runs forever. **It never
  connects to the brain.** (Bubbles = oxygen for the roots; you never want the
  software able to turn this off.)
- **The bucket kit** — the bucket, a mesh "net pot" lid, a bag of clay pebbles.
- **Power + glue** — the **12V wall brick**, a **barrel-jack screw adapter** (a
  little plug with two screw terminals), the **breadboard**, jumper wires, a
  soldering iron + solder, heat-shrink.

Got them all? Good. Build order: **A** brain → **B** breadboard backbone →
**C** dosing pump → **D** light → **E** thermometer → **F** pH → **G** air → 
**H** bucket → **power on**.

---

## Component A — The Brain

Goal: get the XIAO soldered, flashed, and showing up in Home Assistant. When this
works, you have something you can click that controls real pins.

**A1. Solder the pins on (skip if already attached).**
If the XIAO came with two loose black strips of pins, sit the chip on the
breadboard with the pins poking up through its holes (the breadboard holds them
straight for you), then solder each pin to the board — touch the iron to the pin
and the pad together for a second, feed a touch of solder, done. You're soldering
so the chip can sit in the breadboard and connect to wires.

**A2. Note where the labels are.** The pin names (`D0`, `D1`, `GND`, `3V3`,
`5V`...) are printed on the **back** of the XIAO. Flip it over to read them. Keep
a photo on your phone so you don't keep flipping it.

**A3. Flash the firmware.** Plug the XIAO into the build host with a USB-C cable and run:

```
esphome run ~/projects/eden/esphome/eden-z1.yaml
```

Pick the USB device when it asks. If it complains about `wifi_ssid` /
`wifi_password`, you just need to put your WiFi name and password in the ESPHome
secrets file — that's the only thing it needs from you.

**A4. Confirm it's alive.** Open Home Assistant. Within a minute it should
discover a new device, **Eden z1**, with entities including a switch called
`eden z1 ph down dose` and a light called `eden z1 grow light`. If you see those,
the brain works.

**Set the brain aside** (leave it on the breadboard, plugged into USB).

---

## Component B — The Breadboard Backbone

Goal: build the two rails everything else plugs into. Five minutes, no parts
except the brain and two jumper wires, but it's the spine of the whole build.

**B1.** Make sure the XIAO is sitting in the breadboard (from A1), straddling the
center gap, with its pins in the holes.

**B2. Build the +3.3V rail.** Run one jumper wire from the XIAO's **`3V3`** pin to
the breadboard's **red `+` rail**. That whole red rail is now "3.3 volts," ready
to power the small sensors.

**B3. Build the GND rail.** Run one jumper wire from any XIAO **`GND`** pin to the
breadboard's **blue `−` rail**. That whole blue rail is now "ground" — the common
floor. This is the rail the 12V brick will also shake hands with later.

That's it. Two wires, two live rails. **Set aside.**

---

## Component C — The Dosing Pump (your first real win)

Goal: press a button in Home Assistant and watch the pump spin for exactly 2
seconds and stop itself. No liquid yet — just watch the motor turn.

First, meet the **MOSFET board**. It has two ends:
- The **3-pin end** (`SIG`, `VCC`, `GND`) is the *control* side — it listens to
  the brain.
- The **screw-terminal end** has four screws in two pairs: one pair `Vin` / `GND`
  (where the 12V power comes *in*) and one pair `V+` / `V−` (where the *pump*
  connects).

**C1. Plug the 12V brick into the barrel adapter.** Take the wall brick's plug and
push it into the **barrel-jack screw adapter**. Now the brick's power comes out on
two little screw terminals marked `+` and `−`.

**C2. Feed 12V into the MOSFET board:**
- Run a wire from the adapter's **`+`** to the MOSFET board's **`Vin`** screw.
- Run a wire from the adapter's **`−`** to the MOSFET board's **`GND`** screw
  (the one in the `Vin`/`GND` pair).

**C3. Connect the pump:**
- Pump's **red** wire → MOSFET board's **`V+`** screw.
- Pump's **black** wire → MOSFET board's **`V−`** screw.
- (If the pump later runs backwards when you add liquid, just swap these two —
  polarity only sets which way it spins.)

**C4. Connect the control side to the brain:**
- XIAO **`D0`** → MOSFET board **`SIG`**. (This is the brain's "go" signal.)
- XIAO **`GND`** (or the blue GND rail) → MOSFET board **`GND`** (the one in the
  3-pin end). **This is the ground handshake** — without it the switch does
  nothing.
- Leave the MOSFET board's **`VCC`** pin empty. Not used.

**C5. Make the 12V brick join the common floor.** Run one wire from the adapter's
**`−`** to the breadboard's **blue GND rail**. Now the brain's ground and the
brick's ground are the same floor. (The heavy pump current actually flows brick →
pump → brick directly through the screw terminals; this little wire just makes the
grounds agree so the signal is understood.)

**C6. Test it.**
1. XIAO still powered by USB; 12V brick plugged into the wall.
2. In Home Assistant, flip the **`eden z1 ph down dose`** switch **on**.
3. The pump spins — and about **2 seconds later the firmware shuts it off by
   itself**, and the switch flips back to off in HA on its own.

If it spins and auto-stops at 2 seconds: **you've proven the entire control + safety
chain.** That 2-second cutoff is the firmware "reflex" that protects the plant even
if the software goes haywire.

- Nothing happens? 9 times out of 10 it's the **ground handshake** (C4 second
  bullet or C5).
- Spins but *doesn't* stop at 2s? Stop and tell me — the safety cap isn't firing.

**Set the pump module aside** (leave it wired).

---

## Component D — The Grow Light

Goal: a second switch board, this time for the LED strip, dimmable and on a
day/night schedule. This is where you solder two wires.

**D1. Solder leads to the strip.** Look at the cut end of the LED strip — you'll
see two little copper pads marked **`+`** and **`−`**. Solder a wire to each
(slide a bit of heat-shrink over each first, then shrink it over the joint so the
bare metal is covered). You solder because the strip has no connector.

**D2. Take the second MOSFET board** and wire its power exactly like the pump's:
- 12V adapter **`+`** → MOSFET **`Vin`**
- 12V adapter **`−`** → MOSFET **`GND`** (the `Vin`/`GND` pair)
  (You can pigtail off the same 12V adapter that feeds the pump — both muscles
  share the one brick.)

**D3. Connect the strip:**
- Strip **`+`** wire → MOSFET **`V+`**
- Strip **`−`** wire → MOSFET **`V−`**

**D4. Control side to the brain:**
- XIAO **`D1`** → MOSFET **`SIG`**
- Blue GND rail → MOSFET 3-pin **`GND`**
- `VCC` empty.

**D5. Test.** In Home Assistant, find the **`eden z1 grow light`** light entity and
turn it on / drag the brightness. The strip should light and dim. The firmware
also runs it on a schedule by itself — **on at 6:00, off at 20:00** (a 14-hour
"day") — so even with no software it keeps a sane day/night for the plant.

> Honest note: the brain speaks at 3.3V and these MOSFETs would prefer ~10V to
> open fully. The tiny pump doesn't care. The light pulls more current, so touch
> the silver block after a few minutes — if it's hot, tell me and we'll add one
> cheap transistor to drive the gate harder. If it's just warm, fine.

**Set aside.**

---

## Component E — The Thermometer (water temp)

Goal: a live water-temperature reading in Home Assistant. Easiest sensor.

**E1.** The DS18B20 has a small adapter board with three wires. Connect:
- **red** → +3.3V rail
- **black** → GND rail
- **yellow** (data) → XIAO **`D2`**

(The BOJACK adapter already has the little "pull-up" resistor built in, so there's
nothing extra to add.)

**E2. Test.** In Home Assistant, look for **`eden z1 water temp`**. Hold the metal
tip in your hand — the number should rise a degree or two. Working.

**Set aside.**

---

## Component F — The pH Section (the fiddly one)

Goal: a calibrated, live pH reading. Two sub-steps: wire it, then teach it what
4.00 and 7.00 actually look like.

Meet the parts: the **pH board** has a round silver screw connector (a "BNC") for
the probe, and a small 3-wire output cable (or 3 screw terminals) labeled for
**power**, **ground**, and **signal**. The **ADS1115** is the translator between
that signal and the brain.

**F1. Attach the probe.** Take the glass probe's screw connector, line up the
notch on the BNC, push and twist a quarter-turn to lock. (Don't force it — it's a
twist-lock, not a thread.)

**F2. Power the pH board** from the rails:
- board **V+ / VCC** → +3.3V rail
- board **GND** → GND rail

**F3. Wire the ADS1115 translator:**
- ADS **`VDD`** → +3.3V rail
- ADS **`GND`** → GND rail
- ADS **`SDA`** → XIAO **`D4`**
- ADS **`SCL`** → XIAO **`D5`**
- (If the ADS came with a loose pin strip, solder it on first so it sits in the
  breadboard — same as you did for the brain.)

**F4. Connect the pH signal into the translator:**
- pH board **signal** output → ADS **`A0`**

**F5. Confirm a raw reading.** In Home Assistant you should now see a pH number.
It'll be *wrong* until calibrated — that's next.

**F6. Calibrate (teach it the two reference points):**
1. Rinse the probe tip in plain water, dab dry.
2. Dip it in the **7.00** bottle, swirl gently, wait ~1 minute for the number to
   settle. Note the raw value.
3. Rinse, dab, dip in the **4.00** bottle, wait ~1 minute, note that raw value.
4. Tell me both raw numbers (or put them into the firmware's calibration lines).
   I'll set the two-point calibration in `eden-zone.yaml` so the reading reads
   true. Right now the firmware has placeholder calibration numbers — yours
   replace them.

**Set aside.** (Keep the probe tip wet — never let it dry out. Park it in plain
water or its storage cap until the bucket's ready.)

---

## Component G — The Air Pump (dumb on purpose)

**G1.** Push the air stone onto the air pump's hose. Drop the stone in the bucket
(later, once there's water). Plug the air pump into the **wall**. That's the whole
job — it runs 24/7 and **never touches the brain or the software**. Constant
bubbles = oxygen to the roots; we deliberately give the software no way to stop it.

---

## Component H — The Bucket (final assembly, now we add water)

**H1.** Rinse a couple handfuls of clay pebbles, put them in the mesh net-pot lid.
**H2.** Fill the bucket with plain water to the line on the gauge.
**H3.** Add nutrients (MaxiGro) per the label dose, stir.
**H4.** Check pH with your now-calibrated probe. Basil likes ~5.5–6.5. If it's
high, this is what the dosing pump is *for* — but for the first fill you can nudge
it by hand with a few drops of pH-Down so the software starts from a good place.
**H5.** Settle the three things into the bucket: the **air stone** (bubbling), the
**temperature probe**, and the **pH probe** — all dangling in the water, not
touching the bottom.
**H6.** Set the lid with the net pot on. Drop your rooted basil plug into the net
pot so its roots reach down toward the water.

---

## Power on — hand it to the Gardener

Everything's wired and wet. Brain on USB, brick in the wall, air pump humming.
In Home Assistant every Eden entity should be live: pH, water temp, the dose
switch, the light. The firmware already keeps the plant safe on its own (2-second
dose cap, 6:00–20:00 light). The last step is letting the Claude Gardener watch the
numbers and make the small daily decisions — that's the software side we've already
built; I'll switch it on once you've got real sensor readings flowing.

You did it. From a box of parts to a plant a model tends.
