
import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.signal import welch

from ppg.filtering import filterSignal
from ppg.exception import BadSignalWarning

def rrCalc(peaklist, sampleRate, dataDict={}):

    peaklist = np.array(peaklist)

    if len(peaklist) > 0:
        if peaklist[0] <= ((sampleRate / 1e3) * 150):
            peaklist = np.delete(peaklist, 0)
            dataDict['ybeat'] = np.delete(dataDict['ybeat'], 0)
    dataDict['peaklist'] = peaklist

    rrList = (np.diff(peaklist) / sampleRate) * 1e3
    rrIndices = [(peaklist[i], peaklist[i+1]) for i in range(len(peaklist) - 1)]
    rrDiff = np.abs(np.diff(rrList))
    rrSqDiff = np.power(rrDiff, 2)
    
    dataDict['rrList'] = rrList
    dataDict['rrIndices'] = rrIndices
    dataDict['rrDiff'] = rrDiff
    dataDict['rrSqDiff'] = rrSqDiff
    
    return dataDict

def rrUpdate(dataDict={}):

    rrSource = dataDict['rrList']
    bPeaklist = dataDict['binaryPeaklist']
    rrList = np.array([rrSource[i] for i in range(len(rrSource)) if bPeaklist[i] + bPeaklist[i+1] == 2])
    rrMask = np.array([0 if (bPeaklist[i] + bPeaklist[i+1] == 2) else 1 for i in range(len(rrSource))])
    rrMasked = np.ma.array(rrSource, mask=rrMask)
    rrDiff = np.abs(np.diff(rrMasked))
    rrDiff = rrDiff[~rrDiff.mask]
    rrSqDiff = np.power(rrDiff, 2)

    dataDict['rrMasklist'] = rrMask
    dataDict['rrListCor'] = rrList
    dataDict['rrDiff'] = rrDiff
    dataDict['rrSqDiff'] = rrSqDiff

    return dataDict

def hrCalc(rrList, measures={}):
    
    measures['bpm'] = round(60e3 / np.mean(rrList))

    return measures

def breathingCalc(rrList, filterCutOff=[0.1, 0.4], measures={}, dataDict={}):

    x = np.linspace(0, len(rrList), len(rrList))
    xNew = np.linspace(0, len(rrList), np.sum(rrList, dtype=np.int32))
    interp = UnivariateSpline(x, rrList, k=3)
    breathing = interp(xNew)

    breathing = filterSignal(breathing, filterCutOff, sampleRate = 1e3, filterType='bandpass', order=2)

    if len(breathing) < 30000:
        frq, psd = welch(breathing, fs=1000, nperseg=len(breathing))
    else:
        frq, psd = welch(breathing, fs=1000, nperseg=np.clip(len(breathing) // 10,
                                                             a_min=30000, a_max=None))
    
    measures['breathingrate'] = round(frq[np.argmax(psd)] * 60)
    dataDict['breathingSignal'] = breathing
    dataDict['psdBreathing'] = psd
    dataDict['frqBreathing'] = frq

    return measures, dataDict