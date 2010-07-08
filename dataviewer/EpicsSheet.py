import os

from DataSheet import DataSheet
#DataSheet = DataSheet.DataSheet
import escan_data as ED
from Exceptions import *

class EpicsSheet(DataSheet):

    def getXData(self, name):
        '''returns a 1D iterable of positioning data for X axis

        Args:
            name: a name from self.data.pos_names'''

        return [ self.data.pos[i] 
                for i in range(len(self.data.pos)) 
                if self.data.pos_names[i][0] == name][0]

    def getXDataNames(self):

        return [ x[0] for x in self.data.pos_names]

    def getYDataNames(self):

        return self.data.sums_names

    def getYData(self, name):
        '''returns a 1D iterable of intensity(?) data for Y axis
        
        Args:
            name: a name from self.data.sums_names'''

        return self.data.get_data(name=name)

    def getData(self, file):

        if not os.path.isfile(file):
            raise IOError(2, "no such file", file)

        rv = ED.escan_data(file=file)
        # escan_data returns successfully regardless of whether it actually
        # opens the file or not, so we have to guess based on what comes back
        if rv.det_names != []:
            return rv
        else: raise FileTypeError(file)

