import os

from Data2DSheet import Data2DSheet
import escan_data as ED
from Exceptions import *

class Epics2DSheet(Data2DSheet):

    def getData(self, name):
        '''returns a 1D iterable of positioning data for X axis

        Args:
            name: a name from self.data.pos_names'''

        return self.data.get_data(name=name)

    def getDataNames(self):

        return self.data.sums_names

    def readData(self, file):

        if not os.path.isfile(file):
            raise IOError(2, "no such file", file)

        rv = ED.escan_data(file=file)
        # escan_data returns successfully regardless of whether it actually
        # opens the file or not, so we have to guess based on what comes back
        if rv.det_names != [] and rv.dimension == 2:
            return rv
        else: raise FileTypeError(file)

