
import numpy as np 
from scipy import fftpack
from scipy.signal import butter, filtfilt, detrend


def detrendData(data):
    detrendedData = detrend(data)
    return detrendedData

def butterLowpass(order, cutOff, sampleRate):
    nyq = 0.5 * sampleRate
    normalCutOff = cutOff / nyq
    b, a = butter(order, normalCutOff, btype='low')
    return b, a

def butterHighpass(order, cutOff, sampleRate):
    nyq = 0.5 * sampleRate
    normalCutOff = cutOff / nyq
    b, a = butter(order, normalCutOff, btype='high')
    return b, a

def butterBandpass(order, lowOff, highOff, sampleRate):
    nyq = 0.5 * sampleRate
    low = lowOff / nyq
    high = highOff / nyq
    b, a = butter(order, [low, high], btype='bandpass')
    return b, a

def thresholdFilter(data, threshold):
    fourier = fftpack.fft(data)
    power = np.abs(fourier)
    freq = fftpack.fftfreq(data.size)
    fourier[ power < threshold] = 0
    filteredData = fftpack.ifft(fourier)
    return filteredData, power, np.abs(freq)

def filterSignal(data, cutOff, sampleRate, filterType, order=1):
    if filterType.lower() == 'lowpass':
        b, a = butterLowpass(order, cutOff, sampleRate)
    elif filterType.lower() == 'highpass':
        b, a = butterHighpass(order, cutOff, sampleRate)
    elif filterType.lower() == 'bandpass':
        assert type(cutOff) == tuple or list or np.array, 'bandpass filter s cutoff must be array or tuple specifying lower and upper bound: [lower, upper].'
        b, a = butterBandpass(order, cutOff[0], cutOff[1], sampleRate)
    else:
        raise ValueError('filtertype: %s is unknown, available are: lowpass, highpass, bandpass' %filterType)

    filteredData = filtfilt(b, a, data)
    
    return filteredData