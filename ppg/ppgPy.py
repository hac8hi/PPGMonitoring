
import numpy as np

from ppg.preprocessing import interpolateClipping
from ppg.dataTools import movingAverage, getSamplerate
from ppg.filtering import filterSignal
from ppg.analysis import rrCalc, hrCalc, breathingCalc, spo2Calc
from ppg.peaksFinding import peaksFit, peaksCheck

def ppgPy(irData, redData, time):

    measures = {}
    dataDict = {}
    
    irData = np.asarray(irData , dtype=np.float64)
    redData = np.asarray(redData, dtype=np.float64)
    time = np.asarray(time, dtype=np.int64)

    sampleRate = getSamplerate(irData, time)

    irData = interpolateClipping(irData,sampleRate)
    redData = interpolateClipping(redData,sampleRate)

    filteredIrData = filterSignal(irData, 2, sampleRate, 'lowpass')
    filteredRedData = filterSignal(redData, 2, sampleRate, 'lowpass')

    movAvg = movingAverage(irData, sampleRate)

    dataDict = peaksFit(filteredIrData, movAvg, sampleRate, dataDict=dataDict)
    dataDict = rrCalc(dataDict['peaklist'], sampleRate, dataDict=dataDict)
    dataDict = peaksCheck(dataDict['rrList'], dataDict['peaklist'], dataDict['ybeat'], dataDict=dataDict)

    dataDict['nPeaks'] = np.shape(dataDict['peaklist'])[0]

    measures = hrCalc(dataDict['rrListCor'], measures=measures)
    measures, dataDict = breathingCalc(dataDict['rrListCor'], measures=measures, dataDict=dataDict)
    measures, dataDict = spo2Calc(filteredIrData, filteredRedData, dataDict['peaklist'], dataDict['nPeaks'], measures=measures, dataDict=dataDict)

    return measures