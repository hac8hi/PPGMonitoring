
import numpy as np

from ppg.analysis import rrCalc, rrUpdate
from ppg.exception import BadSignalWarning

def peaksDetect(data, sampleRate, movAvg, movPerc , dataDict={}):
    
    movAvg = np.array(movAvg)
    mn = np.mean(movAvg / 100) * movPerc
    movAvg = movAvg + mn

    peaksx = np.where((data > movAvg))[0]
    peaksy = data[peaksx]
    peakedges = np.concatenate((np.array([0]),
                                (np.where(np.diff(peaksx) > 1)[0]),
                                np.array([len(peaksx)])))
    peaklist = []

    for i in range(0, len(peakedges)-1):
        try:
            yValues = peaksy[peakedges[i]:peakedges[i+1]].tolist()
            peaklist.append(peaksx[peakedges[i] + yValues.index(max(yValues))])
        except:
            pass
    
    dataDict['peaklist'] = peaklist
    dataDict['ybeat'] = [data[x] for x in peaklist]
    dataDict['rollingMean'] = movAvg
    dataDict = rrCalc(dataDict['peaklist'], sampleRate,
                           dataDict=dataDict)
    dataDict['rrsd'] = np.std(dataDict['rrList'])
    
    return dataDict

def peaksFit(data, movAvg, sampleRate, bpmmin=40, bpmmax=180, dataDict={}):
    
    movPercList = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 300]

    rrsd = []
    validMa = []

    for movPerc in movPercList:
        dataDict = peaksDetect(data, sampleRate, movAvg, movPerc, dataDict=dataDict)
        bpm = ((len(dataDict['peaklist'])/(len(data)/sampleRate))*60)
        rrsd.append([dataDict['rrsd'], bpm, movPerc])

    for rrsd, bpm, movPerc in rrsd:
        if (rrsd > 0.1) and ((bpmmin <= bpm <= bpmmax)):
            validMa.append([rrsd, movPerc])

    if len(validMa) > 0:
        dataDict['best'] = min(validMa, key=lambda t: t[0])[1]
        dataDict = peaksDetect(data, sampleRate, movAvg, min(validMa, key=lambda t: t[0])[1],
                                     dataDict=dataDict)
        return dataDict
    else:
        raise BadSignalWarning("Bad IR Signal")

def peaksCheck(rrList, peaklist, ybeat, dataDict={}):

    rrList = np.array(rrList)
    peaklist = np.array(peaklist)
    ybeat = np.array(ybeat)

    rrMean = np.mean(rrList)
    thirtyPerc = 0.3 * rrMean
    if thirtyPerc <= 300:
        upperThreshold = rrMean + 300
        lowerThreshold = rrMean - 300
    else:
        upperThreshold = rrMean + thirtyPerc
        lowerThreshold = rrMean - thirtyPerc

    remIdx = np.where((rrList <= lowerThreshold) | (rrList >= upperThreshold))[0] + 1

    dataDict['removedBeats'] = peaklist[remIdx]
    dataDict['removedBeatsy'] = ybeat[remIdx]
    dataDict['binaryPeaklist'] = np.asarray([0 if x in dataDict['removedBeats']
                                                  else 1 for x in peaklist])

    dataDict = rrUpdate(dataDict=dataDict)

    return dataDict