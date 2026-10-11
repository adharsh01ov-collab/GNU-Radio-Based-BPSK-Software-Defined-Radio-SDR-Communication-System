# Software-Defined Radio (SDR) Communication System Using GNU Radio

### BPSK Modulation · Noisy Channel Simulation · Constellation Analysis · Real-Time BER Estimation

A software-only digital communication project built in **GNU Radio Companion (GRC)**. It generates random bits, maps them to **BPSK** symbols, passes them through a **simulated noisy channel**, recovers the bits with a simple receiver, displays the received **constellation**, and measures a running **bit-error-rate (BER)**.

![GNU Radio flowgraph](screenshots/flowgraph.png)

> **Project status:** Working baseband simulation. The flowgraph builds and runs, and every plot in this document was captured from a real run at Channel Model noise voltage `2`. No SDR hardware or over-the-air transmission is used. **Please read [Section 13](#13-known-issues-and-the-ber-alignment-problem) before quoting any BER number from this project**: the measured BER of about 0.49 is much higher than theory predicts, and the most likely cause is a bit-alignment problem in the measurement, not just noise.

![Platform](https://img.shields.io/badge/platform-GNU%20Radio%20Companion-blue)
![Modulation](https://img.shields.io/badge/modulation-BPSK-green)
![Type](https://img.shields.io/badge/type-simulation-lightgrey)
![Status](https://img.shields.io/badge/status-working%20baseband%20sim-yellow)

---

## Related Files

| File | Description |
|---|---|
| [`README.md`](README.md) | This document: theory, design, build guide, results, troubleshooting |
| [`applications.txt`](applications.txt) | Practical and educational applications of this project |
| [`output.pdf`](output.pdf) | Detailed explanation of every output plot, one sub-section per output |
| `SDR_Communication_System.grc` | The GNU Radio Companion flowgraph (add this file to the repository) |
| [`screenshots/`](screenshots/) | Flowgraph and output screenshots used in this README |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objectives](#2-objectives)
3. [Background Theory](#3-background-theory)
4. [System Architecture](#4-system-architecture)
5. [Tools and Requirements](#5-tools-and-requirements)
6. [Flowgraph Blocks: Detailed Description](#6-flowgraph-blocks-detailed-description)
7. [Parameters Used](#7-parameters-used)
8. [Step-by-Step Build Guide](#8-step-by-step-build-guide)
9. [How to Run the Project](#9-how-to-run-the-project)
10. [Outputs and Results](#10-outputs-and-results)
11. [Interpreting the Results Together](#11-interpreting-the-results-together)
12. [Expected BER vs Noise (Theory and Cross-Check)](#12-expected-ber-vs-noise-theory-and-cross-check)
13. [Known Issues and the BER Alignment Problem](#13-known-issues-and-the-ber-alignment-problem)
14. [Troubleshooting Guide](#14-troubleshooting-guide)
15. [Suggested Experiments](#15-suggested-experiments)
16. [Limitations](#16-limitations)
17. [Future Improvements and Roadmap](#17-future-improvements-and-roadmap)
18. [Learning Outcomes](#18-learning-outcomes)
19. [Frequently Asked Questions](#19-frequently-asked-questions)
20. [Glossary](#20-glossary)
21. [Repository Structure](#21-repository-structure)
22. [References and Further Reading](#22-references-and-further-reading)
23. [License](#23-license)
24. [Summary](#24-summary)

---

## 1. Project Overview

Wireless systems turn digital information into signals that can travel through a channel. The channel adds noise and distortion, and the receiver has to decide, sample by sample, which bit was sent. When noise is large compared with the signal, some of those decisions are wrong. Measuring how often that happens, the **bit error rate (BER)**, is the standard way to judge the quality of a digital link.

This project builds a simplified **baseband BPSK (Binary Phase Shift Keying) link** in GNU Radio Companion:

1. A **random bit stream** is generated.
2. Each bit is mapped to a **BPSK symbol**: `0 → -1`, `1 → +1`.
3. The symbols pass through a **Channel Model** that adds complex Gaussian noise.
4. The received signal is shown on a **constellation plot**.
5. A **receiver** keeps the real part of each sample and decides `0` or `1` with a zero threshold.
6. The decisions are compared with the original bits using **XOR**.
7. A **moving average** of the XOR output estimates the **BER**.

Everything runs on a normal laptop. No radio hardware, antenna, or licence is needed.

### Why this project is useful

- It makes an abstract topic (modulation, noise, bit errors) **visible**: you can watch two clean points turn into a noisy cloud as noise increases.
- It gives a **reusable BER meter** (XOR + moving average) that works for any hard-decision receiver.
- It is a stepping stone to a fuller modem with pulse shaping, synchronization, and higher-order modulation, and eventually to real SDR hardware.
- It also teaches an important practical lesson: **a measurement chain can be wrong even when every block "works"**, which is exactly what the alignment analysis in Section 13 shows.

## 2. Objectives

- Generate a stream of random binary data.
- Map the data to BPSK symbols.
- Simulate channel noise without requiring radio hardware.
- Visualize the received signal using a constellation plot.
- Recover bit decisions with a simple BPSK receiver.
- Compare transmitted and recovered bits using XOR.
- Estimate BER by averaging the bit-error indicator stream.
- Explore how channel noise affects the constellation and the bit decisions.
- Understand and validate the measurement itself (alignment, window length, statistical accuracy).

---

## 3. Background Theory

This section gives the minimum theory needed to understand the plots. Standard textbooks (see Section 22) cover the details.

### 3.1 Baseband and complex signals

SDR software works with **complex baseband samples**. Each sample has an **in-phase (I)** part, the real component, and a **quadrature (Q)** part, the imaginary component. A sample `a + jb` can be drawn as a point at `(a, b)` on a plane. That plane is the **constellation diagram**.

Working at baseband means the carrier frequency is ignored. The signal is represented by its envelope and phase only. This keeps the simulation simple and fast, and it is how GNU Radio hands samples between most blocks.

### 3.2 Binary Phase Shift Keying (BPSK)

BPSK sends one bit per symbol by switching the **phase** of the carrier between two values 180° apart:

| Bit | Phase | Baseband symbol |
|---|---|---|
| `0` | 180° | `-1 + 0j` |
| `1` | 0° | `+1 + 0j` |

Because the two phases are opposite, the two symbols lie on the real axis at `-1` and `+1`, and the quadrature part is always zero. This gives the **largest possible separation** between two symbols of a given energy, which is why BPSK is among the most noise-robust modulations.

The **decision boundary** is the vertical line at `I = 0`. A received sample with `I ≥ 0` is decided as `1`; otherwise `0`. This is exactly what the Binary Slicer does.

### 3.3 The additive white Gaussian noise (AWGN) channel

The simplest realistic channel model adds noise to the transmitted signal:

```
r[n] = s[n] + w[n]
```

- `s[n]` is the transmitted symbol (`-1` or `+1`).
- `w[n]` is complex Gaussian noise. Its real and imaginary parts are independent and have the same variance.
- "White" means the noise samples are uncorrelated from one sample to the next.

The noise standard deviation controls how far received samples scatter around the ideal points. In this project that scatter is set by the Channel Model's **Noise Voltage** parameter.

### 3.4 How noise causes bit errors

Suppose `+1` is sent. The receiver sees `1 + n`, where `n` is the real part of the noise. The decision is wrong when `1 + n < 0`, that is, when the noise is more negative than `-1`. For Gaussian noise with standard deviation `σ` (per real component) the probability of this is:

```
P(error) = Q(1 / σ)
```

where `Q(x)` is the tail probability of the standard normal distribution:

```
Q(x) = (1/2) · erfc( x / √2 )
```

By symmetry the same probability applies when `-1` is sent, so the BER of BPSK over AWGN with a zero threshold is `Q(1/σ)`.

In terms of energy per bit to noise density, the standard form is:

```
BER = Q( √(2 · Eb/N0) )
```

With symbols of amplitude 1 and noise variance `σ²` per real component, `Eb/N0 = 1 / (2σ²)`, which gives the same result.

### 3.5 Relating GNU Radio "Noise Voltage" to σ

In GNU Radio the Channel Model's **Noise Voltage** sets the amplitude of a complex Gaussian noise source. For a complex noise source the **total** power is `noise_voltage²`, split equally between I and Q. This implies:

```
σ (per component) = noise_voltage / √2
```

Under that assumption, noise voltage `2` gives `σ ≈ 1.414`, so the theoretical BER is `Q(1/1.414) = Q(0.707) ≈ 0.24`, equivalent to `Eb/N0 ≈ -6 dB`.

> **Check this for your version.** The scaling of the noise source can differ between GNU Radio releases. Verify it by feeding a known signal into the Channel Model and measuring the output variance, or by running the zero-noise and low-noise tests in Section 15. The conclusions in Section 13 hold even if the scaling differs somewhat, because a BER of almost exactly 0.5 is far from any plausible theoretical value for a link with unit-amplitude symbols.

### 3.6 Sample rate, bit period, and plot duration

One BPSK symbol (one bit) is sent per sample in this flowgraph, so the **bit rate equals the sample rate**:

| Quantity | Value |
|---|---|
| Sample rate (`samp_rate`) | 32,000 samples/s |
| Bit rate | 32,000 bit/s |
| Bit period | 1 / 32,000 = 31.25 µs |
| Time-sink points | 1,024 |
| Time shown per plot | 1,024 / 32,000 = 32 ms |

This is why every time plot in this project spans about 32 ms.

### 3.7 Estimating BER with XOR and a moving average

**XOR** outputs `1` when its two inputs differ and `0` when they match:

| Transmitted | Recovered | XOR (error?) |
|---|---|---|
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

The XOR stream is therefore an **error indicator**. Averaging it over a window of `L` bits gives the fraction of wrong bits in that window:

```
BER_window = (number of 1s in the last L XOR outputs) / L
```

This project uses `L = 1000`, implemented by a Moving Average block with **length 1000** and **scale 0.001**. The output of such a window is itself a noisy estimate. For a true BER `p`, its standard deviation is about `√( p(1-p) / L )`. At `p = 0.24` and `L = 1000` that is roughly `0.014`; at `p = 0.5` it is about `0.016`. So wobbles of ±0.01 to ±0.02 in the Estimated BER plot are normal statistical fluctuation, and very small error rates (below roughly 0.001) cannot be measured with a 1000-bit window at all.

### 3.7.1 Why alignment matters

The XOR only measures errors if it compares the **same** bit on both inputs. If the recovered stream is delayed by even one sample relative to the reference stream, the two inputs are effectively unrelated random bits, and the XOR output is `1` about half the time **regardless of noise level**. Section 13 explains why this probably affects this flowgraph.

---

## 4. System Architecture

```text
                    TRANSMITTER AND CHANNEL

Random Source (integer 0/1)
          |
          v
Chunks to Symbols (BPSK: 0 -> -1, 1 -> +1)
          |
          v
Channel Model (simulated complex AWGN channel)
          |
          +----------------------> QT GUI Constellation Sink
          |
          v
                         RECEIVER

Complex To Real
          |
          v
Binary Slicer (negative -> 0, non-negative -> 1)
          |
          +----------------------> UChar To Float -> QT GUI Time Sink ("Recovered BPSK Bits")
          |
          v
                     BER ESTIMATION

XOR  <---- original bits (Random Source -> Int To Float -> Float To UChar)
 |
 +-------> UChar To Float -> QT GUI Time Sink ("Raw Error Bits")
 |
 v
UChar To Float -> Moving Average -> QT GUI Time Sink ("Estimated BER")
```

### 4.1 Data-flow summary

| Stage | Input type | Output type | Purpose |
|---|---|---|---|
| Random Source | none | int | Generate random 0/1 data |
| Chunks to Symbols | int | complex | Map bits to BPSK points |
| Channel Model | complex | complex | Add noise |
| Complex To Real | complex | float | Keep the in-phase part |
| Binary Slicer | float | byte | Hard decision |
| Int To Float → Float To UChar | int → float → byte | byte | Prepare the reference bits for XOR |
| XOR | byte, byte | byte | Mark mismatches |
| UChar To Float | byte | float | Convert for plotting/averaging |
| Moving Average | float | float | Estimate BER |

### 4.2 Reference branch

The original-bit comparison branch is built from:

```text
Random Source -> Int To Float -> Float To UChar -> XOR (in0)
Binary Slicer ---------------------------------> XOR (in1)
```

The two conversion blocks exist only because `Random Source` outputs integers while the Binary Slicer outputs bytes, and XOR needs both inputs to be the same type.

---

## 5. Tools and Requirements

| Item | Details |
|---|---|
| Software | GNU Radio Companion (GRC) and the GNU Radio runtime |
| Distribution used | Radioconda on Windows (the run log shows `radioconda\python.exe`) |
| Language | Python (generated automatically by GRC) |
| Interface | QT GUI |
| Hardware | None required (no SDR, antenna, or RF front end) |
| Optional | An RTL-SDR or similar device for the hardware extensions in Section 17 |

Block and property names can vary slightly between GNU Radio versions. If a block name differs in your install, use the search box in GRC (the screenshot shows a search for `qt gui time`) and choose the closest equivalent.

> The console in the screenshot shows the message `qt.qpa.fonts: Unable to open default EUDC font: "EUDC.TTE"`. This is a harmless Windows font warning from Qt and does not affect the simulation. The flowgraph still finishes with `>>> Done`.

---

## 6. Flowgraph Blocks: Detailed Description

### 6.1 Options

Holds global settings for the flowgraph. This project uses **Generate Options: QT GUI** and **Language: Python**, so GRC generates a Python program with a window that hosts the plots.

### 6.2 Variable: `samp_rate`

A shared constant of **32,000** samples per second. Every sink that needs a sample rate (the three time sinks use `32k`) refers to it, so changing it in one place updates the time axes everywhere. In the screenshot the value is shown as `32k` on the block and `32000` in the Variables table.

### 6.3 Random Source

Generates random integers.

| Parameter | Value | Meaning |
|---|---|---|
| Output type | Int | Integer samples |
| Minimum | `0` | Smallest value |
| Maximum | `2` | **Upper bound is exclusive**, so only `0` and `1` are produced |
| Num Samples | `1k` | Length of the random pattern (1,000 samples) |
| Repeat | Yes | The 1,000-sample pattern repeats forever |

**Important:** with *Repeat = Yes* and *Num Samples = 1k*, the "random" data is a fixed 1,000-bit pattern repeated over and over. For long BER measurements it is better to use a large Num Samples (for example `100k` or more) or a true random generator, so the statistics are not tied to one short pattern. For a short demonstration, 1,000 bits is fine.

### 6.4 Chunks to Symbols

Maps each integer input to an output symbol using a lookup table.

| Parameter | Value |
|---|---|
| Input / output | Int → Complex |
| Symbol Table | `-1, 1` |
| Dimension | `1` |

Index `0 → -1` and index `1 → +1`. The outputs are complex numbers with zero imaginary part, so they lie on the I axis of the constellation.

### 6.5 Channel Model

Simulates an imperfect channel. Internally it combines several effects, which GRC exposes as parameters:

| Parameter | Value | Effect |
|---|---|---|
| Noise Voltage | `2` (this run) | Amplitude of additive complex Gaussian noise |
| Frequency Offset | `0` | Carrier frequency offset (none) |
| Epsilon | `1` | Sample-timing offset / fractional resampling control (`1` = no change in rate) |
| Taps | `1` | FIR filter taps (a single tap of 1 = no filtering) |
| Seed | `0` | Random seed for the noise (0 = a fixed seed in this configuration) |
| Block Tag Propagation | No | Whether stream tags are passed through |

**Why this block matters for measurement:** the Channel Model contains a resampling/interpolation stage and a filter stage. Even with neutral settings (epsilon 1, one tap) these stages can introduce a small fixed **delay** to the signal. That delay is the leading suspect for the BER measurement problem described in Section 13.

### 6.6 QT GUI Constellation Sink

Plots complex samples as dots on the I/Q plane. Settings visible in the screenshot: **Number of Points 1.024k**, **Autoscale No**. With Autoscale off, the axes stay fixed at about ±2, so very noisy samples can fall outside the visible window.

### 6.7 Complex To Real

Outputs only the real (in-phase) part of each complex sample. This is needed because the Binary Slicer expects a real-valued input. For BPSK the information is entirely in the I component, so discarding Q loses nothing useful (and also discards half the noise power).

### 6.8 Binary Slicer

A hard-decision block. It compares each input value with zero:

| Input | Output |
|---|---|
| negative | `0` |
| zero or positive | `1` |

The output type is a byte (`uchar`).

### 6.9 Int To Float, Float To UChar

These two blocks (Scale `1`, Bias `0`) convert the original integer bits first to float and then to byte so they match the Binary Slicer's byte output. They do not change the bit values.

### 6.10 XOR

Takes two byte streams, `in0` (reference bits) and `in1` (recovered bits), and outputs `0` for equal bits and `1` for different bits. Its output is the **raw error indicator**.

### 6.11 UChar To Float (three instances)

Converts byte streams to floats. It is used (a) to plot the recovered bits, (b) to plot the raw error bits, and (c) to feed the Moving Average. QT GUI sinks and the Moving Average block work on floats.

### 6.12 Moving Average

Computes a running average of the error indicators.

| Parameter | Value | Meaning |
|---|---|---|
| Length | `1k` (1000) | Window size in samples |
| Scale | `1m` (0.001) | Multiplies the sum; `1/1000` turns the sum into a fraction |
| Max Iter | `4k` | Internal processing-block size limit |
| Length of Vectors | `1` | Operates on scalars |

With these values the output is directly the **fraction of bad bits in the last 1000**, which is the BER estimate. (During troubleshooting the scale was temporarily set to `1` so the output showed the error *count* instead; the correct BER setting is `0.001`.)

### 6.13 QT GUI Time Sink (three instances)

| Name | Shows | Points | Sample rate | Autoscale |
|---|---|---|---|---|
| Recovered BPSK Bits | Binary Slicer decisions | 1.024k | 32k | No |
| Raw Error Bits | XOR output | 1.024k | 32k | Yes |
| Estimated BER | Moving Average output | 1.024k | 32k | Yes |

---

## 7. Parameters Used

Values below are taken from the flowgraph screenshot of the run that produced the outputs in this document.

| Block | Parameter | Value |
|---|---|---|
| Variable | `samp_rate` | `32000` |
| Random Source | Minimum / Maximum | `0` / `2` |
| Random Source | Num Samples / Repeat | `1k` / Yes |
| Int To Float | Scale | `1` |
| Float To UChar | Scale / Bias | `1` / `0` |
| Chunks to Symbols | Symbol Table / Dimension | `-1, 1` / `1` |
| Channel Model | **Noise Voltage** | **`2`** (this run) |
| Channel Model | Frequency Offset / Epsilon / Taps / Seed | `0` / `1` / `1` / `0` |
| Channel Model | Block Tag Propagation | No |
| Moving Average | Length / Scale / Max Iter / Vector Length | `1k` / `1m` (0.001) / `4k` / `1` |
| QT GUI Time Sinks | Number of Points / Sample Rate | `1.024k` / `32k` |
| QT GUI Constellation Sink | Number of Points / Autoscale | `1.024k` / No |

An earlier diagnostic configuration used noise voltage `0.1`, giving two tight clusters at ±1.

---

## 8. Step-by-Step Build Guide

This is a detailed walk-through for recreating the flowgraph from scratch.

### 8.1 Create the flowgraph

1. Launch **GNU Radio Companion**.
2. Choose **File → New → QT GUI** (so the plots appear in a window).
3. Save it as `SDR_Communication_System.grc`.

### 8.2 Set the sample rate

1. In the *Variables* area, edit the default `samp_rate` variable.
2. Set its value to `32000`.

### 8.3 Build the transmitter

1. Search for **Random Source**. Set *Output Type* to `Int`, *Minimum* to `0`, *Maximum* to `2`, *Num Samples* to `1000` (or larger), *Repeat* to `Yes`.
2. Search for **Chunks to Symbols**. Set *Input Type* `Int`, *Output Type* `Complex`, *Symbol Table* `[-1, 1]`, *Dimension* `1`.
3. Connect `Random Source → Chunks to Symbols`.

### 8.4 Add the channel

1. Search for **Channel Model**.
2. Set *Noise Voltage* to `0.1` for a first, clean test, and later to `2` to reproduce the plots in this README.
3. Leave *Frequency Offset* `0`, *Epsilon* `1`, *Taps* `1`.
4. Connect `Chunks to Symbols → Channel Model`.

### 8.5 Add the constellation display

1. Search for **QT GUI Constellation Sink**.
2. Connect `Channel Model → Constellation Sink`.

### 8.6 Build the receiver

1. Add **Complex To Real** and connect `Channel Model → Complex To Real`.
2. Add **Binary Slicer** and connect `Complex To Real → Binary Slicer`.
3. Add **UChar To Float** and connect `Binary Slicer → UChar To Float`.
4. Add a **QT GUI Time Sink** (name it `Recovered BPSK Bits`, type `Float`) and connect the UChar To Float output to it.

### 8.7 Build the reference (original-bit) branch

1. Add **Int To Float** and connect `Random Source → Int To Float`.
2. Add **Float To UChar** and connect `Int To Float → Float To UChar`.

### 8.8 Build the error and BER branch

1. Add **XOR**. Connect `Float To UChar → XOR in0` and `Binary Slicer → XOR in1`.
2. Add another **UChar To Float** and connect `XOR → UChar To Float`.
3. Connect this UChar To Float to a **QT GUI Time Sink** named `Raw Error Bits`.
4. Also connect the same UChar To Float to a **Moving Average** block (*Length* `1000`, *Scale* `0.001`, *Max Iter* `4000`).
5. Connect the Moving Average to a **QT GUI Time Sink** named `Estimated BER`.

### 8.9 Check the connections

- No red (type-mismatched) connections should remain. Port colours must match: complex (blue), float (orange), byte (purple), int (teal).
- Use **Run → Generate** and watch the console for errors.

### 8.10 Run

Press **Run → Execute** (the play button). A window opens with the constellation and the three time plots. Press the stop button to end.

### 8.11 Recommended addition: a Delay block

To make the BER measurement valid, add a **Delay** block on the reference branch (see Section 13), between `Float To UChar` and `XOR in0`, and tune its delay until BER reads `0` at zero noise.

---

## 9. How to Run the Project

**Quick run (if the `.grc` file is in the repository):**

1. Install GNU Radio Companion (for example via Radioconda).
2. Open `SDR_Communication_System.grc`.
3. Press **Run → Execute**.
4. Observe the four displays: constellation, recovered bits, raw error bits, estimated BER.
5. To change the noise level, edit *Noise Voltage* in the Channel Model block and run again.

**From the command line (generated Python):**

GRC writes a Python file next to the `.grc` file (the console shows `SDR_Communication_System.py`). You can run it with the same Python that GNU Radio uses. Only commit the generated Python file to the repository if you intend to maintain it; the `.grc` file is the primary editable source.

> **Compatibility note:** Port types must match. The Channel Model produces complex samples and the Binary Slicer consumes real floats, so `Complex To Real` must sit between them.

---

## 10. Outputs and Results

All images in this section come from **one run with Channel Model noise voltage = 2**. A detailed written explanation of each plot, one sub-section per output, is in [`output.pdf`](output.pdf).

### 10.1 Flowgraph (full view)

![Flowgraph](screenshots/flowgraph.png)

The screenshot shows the complete graph: transmitter and channel on the left, receiver and error chain in the middle, and the three time sinks on the right. The status area at the bottom confirms the run finished (`>>> Done`).

### 10.2 Output 1: Constellation Plot

![Constellation plot](screenshots/constellation_noise2.png)

**What it is:** each dot is one received complex sample, taken straight from the Channel Model output (before any decision).

**What you see:**

- The dots are spread over roughly -2 to +2 on **both** axes (some fall outside the fixed plot window).
- There are **no two separate clusters** and no clear gap around zero. The points form one wide cloud.
- The vertical spread is as large as the horizontal spread. Since the transmitted signal has no quadrature component, all vertical spread is noise, which confirms the noise is complex and affects both axes.

**Interpretation:** the ideal points at -1 and +1 are only 1 unit from the decision boundary, while the noise spreads samples by more than that. A large share of samples therefore land on the wrong side of zero. With noise voltage `0.1` the same plot shows two tight clusters at -1 and +1.

### 10.3 Output 2: Recovered BPSK Bits

![Recovered BPSK bits](screenshots/recovered_bpsk_bits.png)

**What it is:** the receiver's decision stream: the output of the Binary Slicer converted to float for plotting.

**What you see:**

- A dense train of vertical lines. The stream takes only two values (0 and 1). The y-axis appears to span about 0.07 to 0.93 because autoscale is off for this sink.
- Bits switch rapidly and irregularly with no repeating pattern across the 32 ms window.
- Short gaps with no transitions are runs of identical bits, which is normal for random data.

**Interpretation:** the receiver chain produces a clean binary stream. This plot alone cannot show correctness; it needs the original bits for comparison (the XOR stage).

### 10.4 Output 3: Raw Error Bits

![Raw error bits](screenshots/raw_error_bits.png)

**What it is:** the XOR of transmitted and recovered bits. A `1` means a mismatch; a `0` means a match.

**What you see:**

- The trace jumps between 0 and 1 constantly across the entire window.
- Pulses at 1 are very frequent: wide pulses mean consecutive errors, narrow pulses are isolated errors.
- The signal spends roughly as much time at 1 as at 0.

**Interpretation:** a reliable link would show a mostly flat line at 0 with rare spikes. This trace is the opposite, so many compared bits disagree.

### 10.5 Output 4: Estimated BER

![Estimated BER](screenshots/estimated_ber.png)

**What it is:** the Moving Average of the raw error bits: the fraction of wrong bits in the most recent 1000 bits.

**What you see:**

- A smooth curve between about **0.48 and 0.50** for the whole 32 ms.
- Slow wobbles of about ±0.01, consistent with the statistical fluctuation of a 1000-bit window (Section 3.7).

**Interpretation:** a BER of 0.5 is the performance of random guessing. See Section 13 for why this is higher than theory and what to do about it.

### 10.6 Summary table

| Output | Tapped at | What it shows | Observation at noise voltage 2 |
|---|---|---|---|
| Constellation | Channel Model output | Received I/Q samples | One diffuse cloud, no distinct clusters |
| Recovered Bits | Binary Slicer output | Receiver decisions | Dense, random-looking 0/1 switching |
| Raw Error Bits | XOR output | Per-bit mismatch | Frequent `1` pulses across the window |
| Estimated BER | Moving Average output | Error fraction (last 1000 bits) | About 0.48 to 0.50 |

### 10.7 Earlier low-noise observation

In an earlier run at noise voltage `0.1`, the constellation showed two clear clusters at -1 and +1. A screenshot of that run is not included here. To add one, run with noise `0.1`, capture the constellation window, save it as `screenshots/constellation_low_noise.png`, and embed it with:

```markdown
![Constellation at low noise](screenshots/constellation_low_noise.png)
```

---

## 11. Interpreting the Results Together

Reading the four outputs in order tells one story:

1. **Constellation:** the noise is large compared with the signal, so many samples cross the decision boundary.
2. **Recovered bits:** the receiver produces a clean, valid binary stream, so the chain works mechanically.
3. **Raw error bits:** the comparison finds mismatches throughout the window.
4. **Estimated BER:** the mismatch rate is about 0.49.

Points 1 to 3 agree that the link is poor at noise voltage 2. But point 4 is **higher than the roughly 0.24 expected from theory**, which means the measured number should not be treated as the true performance of BPSK at this noise setting until the alignment check in Section 13 has been done.

**What can be claimed from the current results**

- The simulation runs and all four displays work.
- Increasing noise visibly degrades the constellation and produces many bit errors.
- The numeric BER (about 0.49) should **not** be quoted as the BPSK performance at noise voltage 2 until bit alignment has been verified.

---

## 12. Expected BER vs Noise (Theory and Cross-Check)

The table below shows the **theoretical** BER for BPSK over AWGN, `Q(1/σ)`, with `σ = noise_voltage / √2` (the scaling assumption from Section 3.5), alongside a separate **numerical cross-check**: a short Python/NumPy simulation of 2,000,000 random bits with perfect alignment, and the same simulation with the reference stream shifted by one sample.

| Noise voltage | σ per component | Eb/N0 (dB) | Theoretical BER | Simulated, aligned | Simulated, 1-sample shift |
|---:|---:|---:|---:|---:|---:|
| 0.1 | 0.071 | 20.00 | ≈ 0 | 0.00000 | 0.49946 |
| 0.3 | 0.212 | 10.46 | ≈ 0 | 0.00000 | 0.49946 |
| 0.5 | 0.354 | 6.02 | 0.00234 | 0.00237 | 0.49948 |
| 0.7 | 0.495 | 3.10 | 0.02168 | 0.02174 | 0.49950 |
| 1.0 | 0.707 | 0.00 | 0.07865 | 0.07835 | 0.49941 |
| 1.5 | 1.061 | -3.52 | 0.17289 | 0.17312 | 0.49968 |
| 2.0 | 1.414 | -6.02 | 0.23975 | 0.23977 | 0.49989 |

**How to read the table**

- The *aligned* simulation matches theory closely, confirming the formula and the noise scaling assumption.
- The *1-sample shift* column is about 0.50 for **every** noise level, even when noise is tiny. A BER that stays near 0.5 regardless of noise is the signature of misaligned bit streams.
- The BER you measured at noise voltage 2 is about 0.49, much closer to the "shifted" column (≈ 0.4999) than to the aligned theoretical value (≈ 0.24).

> This cross-check is an independent NumPy model, **not** a measurement of your GRC flowgraph. It shows what the numbers should look like; it does not prove the cause of the 0.49 in your run. Use the zero-noise test in Section 13 to confirm.

### 12.1 Python script used for the cross-check

```python
import numpy as np
from math import erfc, sqrt, log10

Q = lambda x: 0.5 * erfc(x / sqrt(2))      # Gaussian tail probability
rng = np.random.default_rng(1)
N = 2_000_000
bits = rng.integers(0, 2, N)
sym = 2 * bits - 1.0                        # 0 -> -1, 1 -> +1

print("noise_v  sigma/comp  EbN0_dB  theory   sim_aligned  sim_shift1")
for v in (0.1, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0):
    s = v / np.sqrt(2)                      # assumed per-component sigma
    rx = sym + s * rng.standard_normal(N)   # real part of the received sample
    dec = (rx >= 0).astype(int)             # binary slicer
    ber = np.mean(dec != bits)              # aligned comparison
    ber_shift = np.mean(dec[1:] != bits[:-1])   # one-sample misalignment
    th = Q(1 / s)
    print(f"{v:6.1f}  {s:9.3f}  {-20*log10(v):7.2f}  {th:.5f}  {ber:.5f}      {ber_shift:.5f}")
```

Save it as `ber_check.py` and run `python ber_check.py`. It needs only NumPy.

---

## 13. Known Issues and the BER Alignment Problem

### 13.1 The symptom

The Estimated BER plot reads about **0.49** at noise voltage 2. Random guessing gives 0.5. Theory for aligned BPSK at this noise level (under the Section 3.5 scaling) predicts about **0.24**.

### 13.2 The likely cause

The BER is computed by XOR-ing two streams:

- **Reference stream:** `Random Source → Int To Float → Float To UChar → XOR`. This path goes directly to the XOR.
- **Recovered stream:** `Random Source → Chunks to Symbols → Channel Model → Complex To Real → Binary Slicer → XOR`. This path goes through the Channel Model.

The Channel Model includes a fractional-resampling (interpolation) stage and a filter. Those stages add a small fixed **delay** of a few samples. The reference stream has no matching delay, so at any instant the XOR compares bit *n* of the reference with bit *n − d* of the recovered stream. With random data these are unrelated, so the XOR is `1` about half the time whatever the noise, which matches the measured 0.49.

> This is a **hypothesis** based on the block settings, the plots, and the NumPy cross-check. It has not been confirmed on the actual flowgraph. The test below settles it.

### 13.3 How to verify

1. Set Channel Model **Noise Voltage = 0** and run.
2. Look at **Estimated BER**:
   - **Reads about 0** → the streams are aligned. Then the 0.49 at noise 2 is a real noise result, and you should re-check the noise scaling (Section 3.5), because it would not match theory.
   - **Still reads about 0.5** → the streams are misaligned. Continue to the fix.

### 13.4 How to fix

1. Add a **Delay** block on the reference branch, between `Float To UChar` and `XOR in0`.
2. Set its *Delay* to a small number of samples and run at **noise 0**.
3. Try values (for example 1, 2, 3, … 8) until Estimated BER drops to exactly 0.
4. Keep that delay, set noise back to `2`, and compare the new BER with about 0.24.
5. If the Delay value you need is not constant between runs, increase the logic: add a **correlation-based alignment** or send a known **preamble** (see Section 17).

An alternative that avoids the Channel Model delay entirely is to build the noisy channel from basic blocks: `Add` plus `Noise Source` (complex Gaussian). That gives a channel with zero delay, so no `Delay` block is needed.

### 13.5 Other measurement cautions

- **Short repeating pattern.** Random Source with 1,000 samples and Repeat on produces a repeating 1,000-bit pattern, not independent random bits. Use a larger *Num Samples* for BER curves.
- **Window size.** A 1000-bit window has a standard deviation of about ±0.015 near BER 0.5 and cannot resolve BER values much below 0.001.
- **Plot window.** The 1,024-point sinks show only 32 ms. Long-run averages need a longer observation (for example a Vector Sink or a Probe block).
- **Noise voltage is not SNR.** It is a model parameter; convert with `Eb/N0 = 1/noise_voltage²` (valid for unit-amplitude BPSK under the Section 3.5 scaling).

---

## 14. Troubleshooting Guide

| Problem | Likely cause | Fix |
|---|---|---|
| Red connection line between blocks | Port types do not match | Insert a conversion block (for example `Complex To Real`, `UChar To Float`) |
| Binary Slicer will not connect to Channel Model | Channel Model is complex, slicer expects float | Add `Complex To Real` between them |
| XOR will not connect to the original bits | Types differ (int vs byte) | Use `Int To Float → Float To UChar` on the reference branch |
| Estimated BER is a flat line near 0 | Plot scale is wrong, or BER really is near 0 | Check the Moving Average *Scale* is `0.001` and the y-range is wide enough |
| Estimated BER plot seems empty | Moving Average Scale `0.001` makes values tiny, and the y-axis is fixed | Use Autoscale = Yes or widen the y-range; temporarily set Scale `1` to see the error count |
| Estimated BER around 0.5 at all noise levels | Misaligned streams | Follow Section 13.3 and 13.4 |
| Constellation shows only two points | Noise is very low or zero | Raise the Noise Voltage |
| Constellation points outside the window | Autoscale off, fixed axes | Turn Autoscale on or widen the axes |
| No window appears | Generate Options is not QT GUI | Set *Options → Generate Options* to `QT GUI` |
| Console warning about `EUDC.TTE` font | Windows font issue in Qt | Harmless; ignore it |
| Plots freeze or stutter | Too many samples/sec for the GUI | Lower `samp_rate`, or reduce the number of points |
| Recovered bits plot looks like a thick block | Time span is long compared with bit period | Reduce *Number of Points* to zoom in on individual bits |

---

## 15. Suggested Experiments

### Experiment 1: Zero-noise sanity check

- Set Noise Voltage `0`.
- Expect: two points exactly at -1 and +1, and Estimated BER `0` (once aligned).
- Purpose: verifies that the whole chain, including alignment, is correct.

### Experiment 2: Low-noise run

- Noise Voltage `0.1` to `0.3`.
- Expect: two tight clusters, BER about 0.
- Purpose: shows BPSK's robustness when noise is small.

### Experiment 3: Moderate noise

- Noise Voltage `0.7` to `1.0`.
- Expect: two overlapping clusters, BER around 0.02 to 0.08 (Section 12).
- Purpose: the interesting region where errors appear but the clusters are still visible.

### Experiment 4: High noise (this README's run)

- Noise Voltage `2`.
- Expect (aligned): one broad cloud, BER about 0.24.
- Purpose: shows how errors dominate when noise exceeds the signal.

### Experiment 5: BER-vs-noise table

Run the flowgraph at noise voltages such as 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, wait until the Estimated BER settles, and record the value for each in a table like:

| Noise voltage | Measured BER | Theoretical BER |
|---:|---:|---:|
| 0.5 | | 0.00234 |
| 0.7 | | 0.02168 |
| 1.0 | | 0.07865 |
| 1.5 | | 0.17289 |
| 2.0 | | 0.23975 |

Plot measured against theoretical on a log scale to see how closely your flowgraph follows theory.

### Experiment 6: Introduce a deliberate delay

Add a `Delay` block (1 sample) on the reference branch at noise 0. BER should jump to about 0.5. Reducing it back to the correct value should restore BER 0. This proves the effect of misalignment directly.

### Experiment 7: Change the symbol table

Change the table to `[-2, 2]`. The constellation points move to ±2. For the same noise voltage the BER falls, because signal energy rises. Compare with `Eb/N0 = A² / noise_voltage²` for amplitude `A`.

---

## 16. Limitations

- This is a **baseband software simulation**, not an over-the-air RF link.
- The channel is simplified AWGN. It does not model multipath fading, interference, phase noise, or RF hardware impairments.
- The receiver assumes perfectly aligned samples. There is **no timing recovery, carrier recovery, or frame synchronization**.
- One bit is sent per sample, with **no pulse shaping or matched filter**.
- BER is estimated over a **finite 1000-bit moving window**, so the displayed value fluctuates and cannot resolve very small error rates.
- The random data repeats every 1,000 bits with the current Random Source settings.
- **The measured BER (about 0.49) has not been validated** and is probably affected by stream misalignment (Section 13).
- No BER-versus-noise table has been recorded.
- An interactive noise slider was planned but is not part of the verified implementation.

---

## 17. Future Improvements and Roadmap

### Short term

- [ ] Align reference and recovered bits (Delay block) and confirm BER = 0 at zero noise.
- [ ] Increase Random Source length so the data does not repeat every 1,000 bits.
- [ ] Add a `QT GUI Range` slider for interactive noise control.
- [ ] Record a BER-vs-noise table and compare it with theory (Section 12).
- [ ] Add the low-noise constellation screenshot.

### Medium term

- [ ] Add root-raised-cosine pulse shaping with a matched filter.
- [ ] Add symbol-timing recovery and carrier-phase/frequency recovery.
- [ ] Use a preamble and correlation for automatic frame/bit alignment.
- [ ] Automate BER sweeps and save results to a CSV file for plotting.
- [ ] Add a long-run BER block (a running total of errors divided by total bits).

### Long term

- [ ] Extend to **QPSK** and higher-order QAM.
- [ ] Add fading channels (Rayleigh/Rician) and equalization.
- [ ] Add forward error correction and show coding gain.
- [ ] Connect real SDR hardware, for example an RTL-SDR for receive-only experiments, or a supported transceiver for permitted transmit/receive tests.

---

## 18. Learning Outcomes

Working through this project gives practice with:

- Digital modulation and complex baseband representation
- BPSK mapping, decision boundaries, and constellation diagrams
- The AWGN channel and how noise causes bit errors
- The BPSK BER formula `Q(√(2Eb/N0))` and its use
- Data-type compatibility between GNU Radio blocks (complex, float, byte, int)
- XOR-based error detection and moving-average BER estimation
- The statistical accuracy of finite-window estimates
- Debugging a signal chain by inspecting intermediate plots
- Recognising and diagnosing a **measurement** problem (stream misalignment) rather than a signal problem

---

## 19. Frequently Asked Questions

**Q1. Why is the quadrature part always zero in the transmitted signal?**
BPSK only uses two phases, 0° and 180°, which lie on the real axis. All vertical spread seen on the constellation is therefore noise.

**Q2. Why does the Random Source have Maximum = 2 if only 0 and 1 are needed?**
The maximum is exclusive in this block, so `Minimum 0, Maximum 2` yields the values 0 and 1.

**Q3. Why convert the original bits to float and back to byte?**
Because the Random Source outputs integers while the Binary Slicer outputs bytes, and XOR needs matching types. The conversions do not change the values.

**Q4. Why is the Estimated BER about 0.49 instead of 0.24?**
Most likely the two XOR inputs are offset in time by a few samples (the Channel Model adds a small delay), so unrelated bits are compared. See Section 13.

**Q5. How do I know the measurement is correct?**
Set noise to 0. A correct, aligned chain gives BER 0. If it does not, fix the alignment first.

**Q6. Is noise voltage the same as SNR?**
No. It is a model parameter. For unit-amplitude BPSK and the Section 3.5 scaling, `Eb/N0 = 1 / noise_voltage²`, so noise 2 corresponds to about -6 dB.

**Q7. Why does the BER curve wobble?**
A 1000-bit window gives an estimate with a standard deviation of about 0.015 near BER 0.5. Small wobbles are expected.

**Q8. Can this project transmit over the air?**
Not as built. It is a baseband simulation. Hardware extensions would need a suitable SDR and compliance with local radio regulations.

**Q9. Why is the Recovered BPSK Bits plot y-axis not exactly 0 to 1?**
Autoscale is off for that sink, so the displayed range is a fixed approximate window.

**Q10. Why use a Moving Average instead of counting errors?**
It gives a continuously updated, easy-to-plot estimate over the most recent bits, and it needs only one block.

**Q11. What does the `EUDC.TTE` console message mean?**
It is a Qt font warning on Windows. It does not affect the simulation.

**Q12. How can I get a more accurate BER?**
Use a longer window or a cumulative counter, more bits, a non-repeating data source, and make sure the streams are aligned.

---

## 20. Glossary

| Term | Meaning |
|---|---|
| **AWGN** | Additive White Gaussian Noise, the standard simple noise model |
| **Baseband** | A signal represented around zero frequency, without a carrier |
| **BER** | Bit Error Rate: wrong bits divided by total bits |
| **BPSK** | Binary Phase Shift Keying: one bit per symbol using two phases 180° apart |
| **Constellation** | A plot of complex samples on the I/Q plane |
| **Decision boundary** | The threshold separating two decisions (I = 0 for BPSK) |
| **Eb/N0** | Energy per bit divided by noise power spectral density |
| **GRC** | GNU Radio Companion, the graphical flowgraph editor |
| **Hard decision** | Choosing 0 or 1 directly from a sample, without soft information |
| **I / Q** | In-phase (real) and quadrature (imaginary) components |
| **Moving average** | Average over the most recent N samples |
| **Q function** | Tail probability of the standard normal distribution |
| **SDR** | Software-Defined Radio |
| **Symbol** | The unit sent per channel use (one bit in BPSK) |
| **XOR** | Exclusive OR: 1 when inputs differ, 0 when equal |

---

## 21. Repository Structure

```text
sdr-bpsk-communication-system/
├── README.md
├── applications.txt
├── output.pdf
├── SDR_Communication_System.grc      <- add your flowgraph file
├── ber_check.py                      <- optional: the NumPy cross-check from Section 12.1
├── screenshots/
│   ├── flowgraph.png
│   ├── constellation_noise2.png
│   ├── recovered_bpsk_bits.png
│   ├── raw_error_bits.png
│   └── estimated_ber.png
└── LICENSE
```

---

## 22. References and Further Reading

- GNU Radio documentation and tutorials (the project wiki, including the guided tutorials on flowgraphs, QT GUI sinks, and digital modulation).
- J. G. Proakis and M. Salehi, *Digital Communications*, for BPSK, AWGN, and BER derivations.
- B. Sklar, *Digital Communications: Fundamentals and Applications*, for practical treatment of BER and Eb/N0.
- S. Haykin, *Communication Systems*, for baseband and passband signal representation.
- Your own course notes on digital communication, if you are building this as part of a lab or project.

---

## 23. License

Add a `LICENSE` file to the repository (for example MIT or Apache-2.0) and state the chosen licence here. Until then, all rights remain with the author.

---

## 24. Summary

This project demonstrates a foundational SDR communication chain in GNU Radio Companion: random bit generation, BPSK mapping, noisy-channel transmission, receiver decisions, constellation visualization, and a moving-average BER estimator. The captured outputs show the whole chain working, and they also reveal something just as valuable: a measured BER of about 0.49 that is far above the theoretical value of about 0.24, pointing to a bit-alignment problem in the measurement. Fixing that alignment (Section 13), recording a proper BER-vs-noise table (Section 15), and then adding pulse shaping, synchronization, QPSK, and eventually SDR hardware gives a clear path from this learning project to a more complete wireless modem.
