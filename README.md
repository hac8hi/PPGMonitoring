# PPGMonitoring

A desktop application built with **PyQt5** and **pyqtgraph** that displays real-time physiological signals, including **PPG (Photoplethysmography)**, **heart rate (BPM)**, and **breath rate**.

## 🧠 Overview

This app connects to a **microcontroller** via **UDP over Wi-Fi** and uses **CBOR** decoding to retrieve two raw signal channels and their associated timestamps. These signals are then processed and visualized in real time.

### Output Measures:

* **Heart Rate (BPM)**
* **Breathing Rate**

## ✨ Features

* Real-time waveform plotting using `pyqtgraph`
* Interactive and smooth GUI built with `PyQt5`
* Signal acquisition over Wi-Fi using UDP + CBOR
* Modular processing pipeline with clear outputs:

  ```python
  {
    "bpm": <HeartRate>,
    "breathingrate": <BreathRate>
  }
  ```

## 📆 Dependencies

* Python 3.8+
* PyQt5
* pyqtgraph
* numpy
* scipy
* scikit-learn
* cbor2
* socket (standard lib)

Install via pip:

```bash
pip install pyqt5 pyqtgraph numpy scipy scikit-learn cbor2
```

## ⚙️ How It Works

1. A **microcontroller** sends:

   * Two PPG signal channels
   * A timestamp array
   * All encoded with **CBOR**, over **UDP Wi-Fi**
2. The app decodes and forwards the data to the `ppgPy.py` module.
3. The signal is filtered, analyzed, and visualized.

---

## 🧪 Signal Processing (`ppgPy.py`)

This module handles all the physiological signal processing. Here's the step-by-step pipeline:

1. **Conversion**:
   Incoming signals (`signal1`, `signal2`, `time`) are converted into NumPy arrays.

2. **PCA Flattening**:
   The two PPG signals are flattened into a single representative signal using **Principal Component Analysis (PCA)**.

3. **Sampling Rate Calculation**:
   The sampling frequency is derived from the time array and used in further processing.

4. **Filtering**:
   A **Butterworth low-pass filter** with a cutoff around **2 Hz** (configurable) is applied to remove high-frequency noise.

5. **Peak Detection**:
   Peaks (heartbeats) are detected from the filtered signal to compute **R-R intervals**.

6. **Measure Extraction**:

   * **Heart Rate (BPM)** is computed from the R-R intervals.
   * **Breathing Rate** is estimated based on modulation in the signal amplitude or frequency.

7. **Return Structure**:

   ```python
   {
     "bpm": <float>,              # Heart rate in beats per minute
     "breathingrate": <float>     # Breathing rate in breaths per minute
   }
   ```

---

## 🚀 Running the App

1. Ensure your microcontroller is sending data over UDP to your computer's IP and expected port.
2. Launch the app:

```bash
python main.py
```

3. You should see:

   * Live waveforms
   * Real-time BPM and breathing rate updates

---

## 📡 Microcontroller Data Format

Expected CBOR-encoded structure:

```python
{
  "time": list[float],
  "signal1": list[float],
  "signal2": list[float]
}
```

---
