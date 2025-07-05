
import numpy as np
from scipy.interpolate import UnivariateSpline

def markClipping(data, threshold=3.29):

    clipBinary = np.where(data > threshold)
    clippingEdges = np.where(np.diff(clipBinary) > 1)[1]

    clippingSegments = []

    for i in range(0, len(clippingEdges)):
        if i == 0: #if first clipping segment
            clippingSegments.append((clipBinary[0][0], 
                                      clipBinary[0][clippingEdges[0]]))
        elif i == len(clippingEdges) - 1:
            #append last entry
            clippingSegments.append((clipBinary[0][clippingEdges[i]+1],
                                      clipBinary[0][-1]))    
        else:
            clippingSegments.append((clipBinary[0][clippingEdges[i-1] + 1],
                                      clipBinary[0][clippingEdges[i]]))

    return clippingSegments


def interpolateClipping(data, sampleRate, threshold=3.29):

    clippingSegments = markClipping(data, threshold)
    numDatapoints = int(0.1 * sampleRate)
    
    for segment in clippingSegments:
        if segment[0] < numDatapoints: 
            #if clipping is present at start of signal, skip.
            #We cannot interpolate accurately when there is insufficient data prior to clipping segment.
            pass
        else: 
            antecedent = data[segment[0] - numDatapoints : segment[0]]
            consequent = data[segment[1] : segment[1] + numDatapoints]
            segmentData = np.concatenate((antecedent, consequent))
        
            interpdataX = np.concatenate(([x for x in range(segment[0] - numDatapoints, segment[0])],
                                            [x for x in range(segment[1], segment[1] + numDatapoints)]))
            xNew = np.linspace(segment[0] - numDatapoints,
                                segment[1] + numDatapoints,
                                ((segment[1] - segment[0]) + (2 * numDatapoints)))
        
            try:
                interpFunc = UnivariateSpline(interpdataX, segmentData, k=3)
                interpData = interpFunc(xNew)
        
                data[segment[0] - numDatapoints :
                     segment[1] + numDatapoints] = interpData
            except:
                #pass over failed interpolation: leave original data alone
                pass
       
    return data