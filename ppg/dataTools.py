
from scipy.ndimage import uniform_filter1d
#from scipy.signal import detrend
#from sklearn.decomposition import PCA

import numpy as np

"""
def pca(data1, data2):
    
    concatData = np.column_stack((data1, data2))
    
    pca = PCA(n_components=1)
    dataCombined = pca.fit_transform(concatData)
    
    return dataCombined.flatten()

def detrendData(data):
    
    data = detrend(data)
    
    return data
"""
def getSamplerate(data, timerData):
    
    sampleRate = ((len(data) / (timerData[-1]-timerData[0]))*1e3)
    
    return sampleRate

def movingAverage(data, sampleRate, windowSize=0.75):

    movAvg = uniform_filter1d(np.asarray(data, dtype='float'), size=int(windowSize*sampleRate))
    
    return movAvg