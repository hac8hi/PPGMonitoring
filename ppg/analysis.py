
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

def spo2Calc(irData, redData, peaklist, nPeaks, measures={}, dataDict={}):
    
    uchSpo2Table = np.array([95, 95, 95, 95, 95, 95, 95, 95, 96, 96, 96, 96, 96, 
                             96, 96, 96, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 
                             97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 
                             98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98,
                             98, 98, 98, 98, 98, 98, 98, 98, 98, 99, 99, 99, 99,
                             99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
                             99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 
                             99, 100, 100, 100, 100, 100, 100, 100, 100, 100, 
                             100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 
                             100, 100, 100, 100, 100, 100, 99, 99, 99, 99, 99, 
                             99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 
                             98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 98, 
                             98, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 96,
                             96, 96, 96, 96, 96, 96, 96, 96, 96, 95, 95, 95, 95, 
                             95, 95, 95, 94, 94, 94, 94, 94, 94])
    iRatioCount = 0
    ratio = []

    # find max between two valley locations
    # and use ratio between AC component of Ir and Red DC component of Ir and Red for SpO2
    
    for k in range(nPeaks-1):
        redDcMax = -16777216
        irDcMax = -16777216
        if peaklist[k+1] - peaklist[k] > 3:
            for i in range(peaklist[k], peaklist[k+1]):
                if irData[i] > irDcMax:
                    irDcMax = irData[i]
                    irDcMaxIndex = i
                if redData[i] > redDcMax:
                    redDcMax = redData[i]
                    redDcMaxIndex = i

            redAc = int((redData[peaklist[k+1]] - redData[peaklist[k]]) * (redDcMaxIndex - peaklist[k]))
            redAc = redData[peaklist[k]] + int(redAc / (peaklist[k+1] - peaklist[k]))
            redAc = redData[redDcMaxIndex] - redAc  # subtract linear DC components from raw

            irAc = int((irData[peaklist[k+1]] - irData[peaklist[k]]) * (irDcMaxIndex - peaklist[k]))
            irAc = irData[peaklist[k]] + int(irAc / (peaklist[k+1] - peaklist[k]))
            irAc = irData[irDcMaxIndex] - irAc  # subtract linear DC components from raw

            nume = redAc * irDcMax
            denom = irAc * redDcMax
            if (denom > 0 and iRatioCount < 5) and nume != 0:
                # original cpp implementation uses overflow intentionally.
                # but at 64-bit OS, Pyhthon 3.X uses 64-bit int and nume*100/denom does not trigger overflow
                # so using bit operation ( &0xffffffff ) is needed
                ratio.append(int((nume * 100) / denom))
                iRatioCount += 1

    # choose median value since PPG signal may vary from beat to beat
    ratio = sorted(ratio)  # sort to ascending order
    midIndex = int(iRatioCount / 2)

    if midIndex > 1:
        ratioAv = int((ratio[midIndex-1] + ratio[midIndex])/2)
    else:
        if len(ratio) != 0:
            ratioAv = ratio[midIndex]

    # why 184?
    # print("ratio average: ", ratio_ave)
    if ratioAv > 2 and ratioAv < 184:
        # -45.060 * ratioAverage * ratioAverage / 10000 + 30.354 * ratioAverage / 100 + 94.845
        spo2 = uchSpo2Table[ratioAv]
        #spo2 = -45.060 * ratioAv ** 2 / 10000 + 30.354 * ratioAv / 100 + 94.845
    else:
        raise BadSignalWarning("Bad Red signal")
    
    measures['spo2'] = round(spo2)
    dataDict['ratioAverage'] = ratioAv

    return measures, dataDict