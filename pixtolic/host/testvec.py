import numpy as np
from PIL import Image

def gradient(color_depth=4):
    lim = 2 ** color_depth
    stepsize = 256 // lim
    arr = np.repeat(
        stepsize * np.arange(lim, dtype='uint8'),
        3 * lim,
    ).reshape((lim, lim, 3))
    return Image.fromarray(arr)

if __name__ == '__main__':
    gradient().show()
