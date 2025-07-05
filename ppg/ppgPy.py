
import numpy as np

from ppg.dataTools import movingAverage, getSamplerate, pca
from ppg.filtering import filterSignal
from ppg.analysis import rrCalc, hrCalc, breathingCalc
from ppg.peaksFinding import peaksFit, peaksCheck

def ppgPy(irData, redData, time):

    measures = {}
    dataDict = {}
    
    irData1 = np.asarray(irData , dtype=np.float64)
    irData2 = np.asarray(redData, dtype=np.float64)
    time = np.asarray(time, dtype=np.int64)

    irData = pca(irData1, irData2)

    sampleRate = getSamplerate(irData, time)

    filteredIrData = filterSignal(irData, 2, sampleRate, 'lowpass')

    movAvg = movingAverage(irData, sampleRate)

    dataDict = peaksFit(filteredIrData, movAvg, sampleRate, dataDict=dataDict)
    dataDict = rrCalc(dataDict['peaklist'], sampleRate, dataDict=dataDict)
    dataDict = peaksCheck(dataDict['rrList'], dataDict['peaklist'], dataDict['ybeat'], dataDict=dataDict)

    measures = hrCalc(dataDict['rrListCor'], measures=measures)
    measures, dataDict = breathingCalc(dataDict['rrListCor'], measures=measures, dataDict=dataDict)

    return measures