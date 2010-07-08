#!/usr/bin/python

import os
import sys
import copy
import time
import json
try:
    import numpy 
except ImportError:
    print "Error: Escan_data can't load numpy"
    sys.exit(1)

try:
    import h5py
    has_h5 = True
except ImportError:
    has_h5 = False
has_h5 = False

class escan_data:
    """ Epics Scan Data """
    mode_names = ('2d', 'epics scan',
                  'user titles', 'pv list',
                  '-----','=====',
                  'scan began at', 'scan ended at',
                  'column labels', 'scan regions','data')
    
    def __init__(self,file='',correct_deadtime=True,**args):
        self.filename    = file
        self.xpos        = ''
        self.ypos        = ''
        self.start_time  = ''
        self.stop_time   = ''
        self.dimension   = 1
        self.user_titles = []
        self.scan_regions= []
        self.pv_list     = []
        self.pos         = []
        self.det         = []
        self.info        = {}
        self.pos_names   = []
        self.det_names   = []

        self.sums       = []
        self.sums_names = []
        self.sums_list  = []
        self.iocr       = None

        self.has_fullxrf = False
        self.xrf_data = []
        self.xrf_energies = []
        self.xrf_header = ''
        
        self.correct_deadtime = correct_deadtime
        self.progress    = None
        self.message     = self.message_printer

        for k in args.keys():
            if (k == 'progress'): self.progress = args[k]
            if (k == 'message'):  self.message  = args[k]
        
        self.x = numpy.array(0)
        self.y = numpy.array(0)
        if self.filename != '':
            self.read_data_file(fname=self.filename)

    def message_printer(self,s,val):
        sys.stdout.write("%s\n" % val)

    def my_progress(self,val):
        sys.stdout.write("%f .. " % val)
        sys.stdout.flush()
#         sys.stdout.flush()
            
    def filetype(self,fname=None):
        """ checks file type of file, returning:
        'escan'  for  Epics Scan
        None     otherwise
        """
        try:
            u = open(fname,'r')
            t = u.readline()
            u.close()
            if 'Epics Scan' in t: return 'escan'

        except IOError:
            pass

        return None

    
    def get_map(self,name=None,norm=None):
        return self.get_data(name=name,norm=norm)

    def get_data(self,name=None,norm=None,icr_correct=True):
        """return data array by name"""
        dat = self._getarray(name,icr_correct=icr_correct)
        if dat is None: return data
        if norm is not None:
            norm = self._getarray(norm,icr_correct=True)
            dat  = dat/norm            
        return dat
    
    def match_detector_name(self, str, strict=False):
        """return index in self.det_names most closely matching supplied string"""
        s  = str.lower()
        sw = s.split()
        b  = [i[0].lower() for i in self.det_names]
        # look for exact match
        for i in b:
            if (s == i):  return b.index(i)
        
        # look for inexact match 1: compare 1st words
        for i in b:
            sx = i.split()
            if (sw[0] == sx[0]):   return b.index(i)

        # check for 1st word in the det name
        if not strict:
            for i in b:
                j = i.find(sw[0])
                if (j >= 0):  return b.index(i)
        # found no matches
        return -1

    def ShowProgress(self,val,row=-1):
        if (self.progress != None):
            self.progress(val)
        elif (row>-1):
            # print " %3i " % (row),
            if (row %10 == 0): print ""

    def ShowMessage(self,val,state='state'):
        if (self.message != None):
            self.message(state,val)

    def PrintMessage(self,s):
        sys.stdout.write(s)
        sys.stdout.flush()
        
    def read_data_file(self,fname=None):
        """generic data file reader"""
        if fname is None: fname = self.filename
        h5name = "%s.h5" % fname
        read_ascii = True
        if has_h5 and os.path.exists(h5name):
            mtime_ascii = os.stat(fname)[8]
            mtime_h5    = os.stat(h5name)[8]
            if mtime_h5 > mtime_ascii:
                retval = self.read_h5file(h5name)
                if retval is None:
                    msg = "file %s read OK" % h5name
                    self.ShowMessage(msg)
                    read_ascii = False

        if read_ascii:
            retval = self.read_ascii(fname=fname)
            if retval is None:
                msg = "file %s read OK" % fname
            else:
                msg = "problem reading file %s" % fname
            self.ShowMessage(msg)
            if has_h5 and retval is None:
                try:
                    self.write_h5file(h5name)
                except:
                    if os.path.exists(h5name):
                        os.unlink(h5name)
        return retval

    def write_h5file(self,h5name):
        try:
            fout = h5py.File(h5name, 'w')
        except:
            print 'write_h5file error??? ', h5name
            

        fout.attrs['Version'] = '1.0.0'
        fout.attrs['Title'] = 'Epics Scan Data'
        fout.attrs['Beamline'] = 'GSECARS / APS'

        g = fout.create_group('scan')
        g['dimension'] = self.dimension
        

        g['stop_time'] = self.stop_time
        g['start_time'] = self.start_time

        g['x'] = self.x
        g['x'].attrs['name'] = self.xpos
        if self.dimension  > 1:
            g['y'] = self.y
            g['y'].attrs['name'] = self.ypos            
            

        g['correct_deadtime'] = repr(self.correct_deadtime)
        attr_list = ['det', 'pos', 'sums']
        if self.iocr is not None:
            attr_list.extend(['iocr', 'det_corr', 'sums_corr'])
        else:
            g['iocr'] = 'False'
        
        for attr in attr_list:
            g.create_dataset(attr, data= getattr(self,attr), compression=5)

        for attr in ('pos_names', 'det_names', 'pv_list',
                     'scan_regions', 'user_titles', 'info',
                     'sums_list', 'sums_names'):
            g[attr] = json.dumps(getattr(self,attr))

        if self.has_fullxrf:
            g = fout.create_group('full_xrf')
            g['header'] = self.xrf_header
            g.create_dataset('data', data= self.xrf_data, compression=5)
            g.create_dataset('energies', data= self.xrf_energies, compression=5)
            g['energies'].attrs['units'] = 'keV'
            
        fout.close()
        return None
        
    def read_h5file(self,h5name):
        f = h5py.File(h5name,'r')

        isValid = False
        attrs  = f.attrs
        try:
            version = f.attrs['Version']
            title   = f.attrs['Title']
            if title  != 'Epics Scan Data': raise KeyError
            beamline = f.attrs['Beamline']
            isValid = True
        except KeyError:
            isValid = False
        if not isValid:
            raise

        g = f['scan']
        self.stop_time  = g['stop_time'].value
        self.start_time = g['start_time'].value
        self.dimension  = g['dimension'].value

        self.x    = g['x'].value
        self.xpos = g['x'].attrs['name']
        self.y    = []
        self.ypos = ''
        if self.dimension > 1:
            self.y = g['y'].value
            self.ypos = g['y'].attrs['name']

        self.correct_deadtime = g['correct_deadtime'].value == 'True'
        if g['iocr'].value == 'False':
            self.iocr = None
            self.det_corr = []
            self.sums_corr = []
            
        attr_list = ['det', 'pos', 'sums']
        if self.iocr is not None:
            attr_list.extend(['iocr', 'det_corr', 'sums_corr'])

        for attr in attr_list:
            setattr(self,attr,  g[attr].value)

        for attr in ('pos_names', 'det_names', 'pv_list',
                     'scan_regions', 'user_titles', 'info',
                     'sums_list', 'sums_names'):
            setattr(self,attr, json.loads(g[attr].value))
        
        self.has_fullxrf = 'full_xrf' in f.keys()
        if self.has_fullxrf:
            g = f['full_xrf']
            self.xrf_header = g['header'].value
            self.xrf_energies = g['energies'].value
            self.xrf_data = g['data'] .value
        f.close()
        return None
        
    def _getarray(self,name=None,icr_correct=True):
        i = None
        arr = None
        if name in self.sums_names:
            i = self.sums_names.index(name)
            arr = self.sums
            if icr_correct: arr = self.sums_corr
        else:
            i = self.match_detector_name(name)
            arr = self.det
            if icr_correct: arr = self.det_corr
        if i is not None:
            return arr[i]
        
        return None
        
                
    def _open_ascii(self,fname=None):
        """open ascii file, return lines after some checking"""
        if fname is None: fname = self.filename
        if fname is None: return None

        self.ShowProgress(1.0)
        self.ShowMessage("opening file %s  ... " % fname)
        try:
            f = open(fname,'r')
            lines = f.readlines()
            lines.reverse()
            f.close()
        except:
            self.ShowMessage("ERROR: general error reading file %s " % fname)
            return None

        line1    = lines.pop()
        if 'Epics Scan' not in line1:
            self.ShowMessage("Error: %s is not an Epics Scan file" % fname)
            return None
        return lines
        
    def _getline(self,lines):
        "return mode keyword,"
        inp = lines.pop()
        is_comment = True
        mode = None
        if len(inp) > 2:
            is_comment = inp[0] in (';','#')
            s   = inp[1:].strip().lower()
            for j in self.mode_names:
                if s.startswith(j):
                    mode = j
                    break
            if mode is None and not is_comment:
                w1 = inp.strip().split()[0]
                try:
                    x = float(w1)
                    mode = 'data'
                except ValueError:
                    pass
        return (mode, inp)
        

    def _make_arrays(self, tmp_dat, col_legend, col_details):
        # convert tmp_dat to numpy 2d array
        dat = numpy.array(tmp_dat).transpose()
        print 'dat: ', dat.shape
        # make raw position and detector data, using column labels
        npos = len( [i for i in col_legend if i.lower().startswith('p')])
        ndet = len( [i for i in col_legend if i.lower().startswith('d')])

        self.pos  = dat[0:npos,:]
        self.det  = dat[npos:,:]

        # parse detector labels
        for i in col_details:
            try:
                key,detail = i.split('=')
            except:
                break
            label,pvname = [i.strip() for i in detail.split('-->')]
            label = label[1:-1]
            if key.startswith('P'):
                self.pos_names.append((label,pvname))
            else:
                self.det_names.append((label,pvname))                
                
        # make sums of detectors with same name and isolate icr / ocr
        self.sums       = []
        self.sums_names = []
        self.sums_list  = []
        self.iocr       = None
        icr,ocr = [],[]
        sum_name = None
        isum = -1
        for i, det in enumerate(self.det_names):
            thisname, thispv = det    
            if 'mca' in thisname and ':' in thisname:
                thisname = thisname.replace('mca','').split(':')[1].strip()
            if thisname != sum_name:
                sum_name = thisname
                self.sums_names.append(sum_name)
                isum  = isum + 1
                self.sums.append( self.det[i][:] )
                self.sums_list.append(i)
                o = [i]
            else:
                self.sums[isum] += self.det[i][:]
                o.append(i)
                self.sums_list[isum] = o
            if 'icr' in thisname.lower(): icr.append(self.det[i][:])
            if 'ocr' in thisname.lower(): ocr.append(self.det[i][:])

        self.sums = numpy.array(self.sums)
        # if icr/ocr data is included, pop them from
        # the detector lists.
        self.info['icr/ocr'] = False
        if len(icr)>0 and len(ocr)==len(icr):
            self.iocr  = numpy.array(icr)/numpy.array(ocr)
            n_icr     = self.iocr.shape[0]
            self.det  = self.det[0:-2*n_icr]
            self.sums = self.sums[0:-2*n_icr]
            self.sums_list  = self.sums_list[:-2*n_icr]
            self.sums_names = self.sums_names[:-2*n_icr]
            self.det_names  = self.det_names[:-2*n_icr]
            self.info['icr/ocr'] = True
            
        if self.dimension == 2:
            ny = len(self.y)
            nx = len(tmp_dat)/ny
            # print self.det.shape, ny, len(tmp_dat), len(tmp_dat)*1.0/ny
            self.det.shape   = (self.det.shape[0],  ny, nx)
            self.pos.shape  = (self.pos.shape[0],  ny, nx)
            self.sums.shape = (self.sums.shape[0], ny, nx)
            if self.iocr is not None:
                self.iocr.shape = (self.iocr.shape[0], ny, nx)
           
            self.x = self.pos[0,0,:]
        else:
            self.x = self.pos[0]
            nx = len(self.x)
            self.y = []

        # finally, icr/ocr corrected sums
        self.det_corr  = copy.deepcopy(self.det)
        self.sums_corr = copy.deepcopy(self.sums)

        if self.info['icr/ocr']:
            idet = -1
            for label,pvname in self.det_names:
                idet = idet + 1
                if 'mca' in pvname:
                    nmca = int(pvname.split('mca')[1].split('.')[0]) -1
                    self.det_corr[idet] *=  self.iocr[nmca]

            isum = -1
            for sumlist in self.sums_list:
                isum  = isum + 1
                if isinstance(sumlist, (list,tuple)):
                    self.sums_corr[isum] = self.det_corr[sumlist[0]]
                    for i in sumlist[1:]:
                        self.sums_corr[isum] += self.det_corr[i]                

                else:
                    self.sums_corr[isum] = self.det_corr[sumlist]

        return
        
    def read_ascii(self,fname=None):
        """read ascii data file"""
        lines = self._open_ascii(fname=fname)
        if lines is None: return -1
        
        maxlines = len(lines)

        iline = 1
        ndata_points = None
        tmp_dat = []
        tmp_y   = []
        col_details = []
        col_legend = None
        ntotal_at_2d = []
        mode = None
        while lines:
            key, raw = self._getline(lines)
            iline= iline+1
            if key is not None and key != mode:
                mode = key

            if (len(raw) < 3): continue
            self.ShowProgress( iline* 100.0 /(maxlines+1))

            if mode == '2d':
                self.dimension = 2
                sx   = raw.split()
                yval = float(sx[2])
                tmp_y.append(yval)
                ypos_name = sx[1]
                mode = None
                if len(tmp_dat)>0:
                    ntotal_at_2d.append(len(tmp_dat))

            elif mode == 'epics scan':             # real numeric column data
                print 'Warning: file appears to have a second scan appended!'
                break
                
            elif mode == 'data':             # real numeric column data
                tmp_dat.append(numpy.array([float(i) for i in raw.split()]))
                
            elif mode == '-----':
                if col_legend is None:   
                    col_legend = lines.pop()[1:].strip().split()

            elif mode == '=====':   
                pass
            
            elif mode == 'user titles':
                self.user_titles.append(raw[1:].strip())

            elif mode == 'pv list':
                self.pv_list.append(raw[1:].strip())
                        
            elif mode == 'scan regions':
                self.scan_regions.append(raw[1:].strip())

            elif mode == 'scan ended at':
                self.stop_time = raw[20:].strip()

            elif mode == 'scan began at':
                self.start_time = raw[20:].strip()

            elif mode == 'column labels':
                col_details.append(raw[1:].strip())

            elif mode is None:
                sx = [i.strip() for i in raw[1:].split('=')]
                if len(sx)>1:
                    self.info[sx[0]] = sx[1]
                    if sx[0] == 'scan dimension':
                        self.dimension = int(float(sx[1]))

            else:
                print 'UNKOWN MODE = ',mode, raw[:20]

        try:        
            col_details.pop(0)
            self.pv_list.pop(0)
        except IndexError:
            print 'Empty Scan File'
            return -2
        
        if len(self.user_titles) > 1: self.user_titles.pop(0)
        if len(self.scan_regions) > 1: self.scan_regions.pop(0)

        # check that 2d maps are of consistent size
        if self.dimension == 2:
            ntotal_at_2d.append(len(tmp_dat))
            np_row0 = ntotal_at_2d[0]
            nrows   = len(ntotal_at_2d)
            npts    = len(tmp_dat)

            if npts != np_row0 * nrows:
                for i,n in enumerate(ntotal_at_2d):
                    if n == np_row0*(i+1):
                        nrows,npts_total = i+1,n

                if len(tmp_y) > nrows or len(tmp_dat)> npts_total:
                    print 'Warning: Some trailing data may be lost!'
                    tmp_y = tmp_y[:nrows]
                    tmp_dat = tmp_dat[:npts_total+1]
            #
        self.y = numpy.array(tmp_y)
        # done reading file
        # print 'read file -> make_arrays ', col_legend, col_details
        # print type(tmp_dat), len(tmp_dat)
        nlast = 0
        oonpts = None
        for irow,jcount in enumerate(ntotal_at_2d):
            # print irow, jcount, oonpts
            if oonpts is None: oonpts = jcount
            if jcount-nlast != oonpts:
                print 'Inconsistent number of points in data!'
                # print irow, jcount,nlast, oonpts
                return
            nlast = jcount
        
        self._make_arrays(tmp_dat,col_legend,col_details)
        tmp_dat = None
        #
        self.has_fullxrf = False        
        if os.path.exists("%s.fullxrf" %fname):
            self.read_fullxrf("%s.fullxrf" %fname, len(self.x), len(self.y))

    def read_fullxrf(self,xrfname, n_xin, n_yin):
        inpf = open(xrfname,'r')

        atime = os.stat(xrfname)[8]
    
        prefix = os.path.splitext(xrfname)[0]
        print 'Reading Full XRF spectra from %s'  % xrfname

        first_line = inpf.readline()
        if not first_line.startswith('; MCA Spectra'):
            print 'Warning: %s is not a QuadXRF File' % xrffile
            inpf.close()
            return
        
        self.has_fullxrf = True
        isHeader= True
        nheader = 0
        header = {'CAL_OFFSET':None,'CAL_SLOPE':None,'CAL_QUAD':None}
        rois   = []

        n_elems    = 4
        n_energies = 2048


        while isHeader:
            line = inpf.readline()
            nheader = nheader + 1        
            isHeader = line.startswith(';') and not line.startswith(';----')
            words = line[2:-1].split(':')
            if words[0] in header.keys():
                header[words[0]] = [float(i) for i in words[1].split()]
            elif words[0].startswith('ROI'):
                roinum = int(words[0][3:])
                rois.append((words[1].strip(),int(words[2]),int(words[3])))


        # end of header: read one last line
        line = inpf.readline()
        ndet = len(header['CAL_OFFSET'])
        nheader = nheader + 1
        # print '==rois==' , len(rois), len(rois)/ndet, ndet
        allrois = []
        nrois =  len(rois)/ndet
        for i in range(nrois):
            tmp = [rois[i+j] for j in range(ndet)]
            allrois.append( tuple(tmp) )


        roi_template ="""ROI_%i_LEFT:   %i %i %i %i
ROI_%i_RIGHT:  %i %i %i %i 
ROI_%i_LABEL:  %s & %s & %s & %s & """
        xrf_header= """VERSION:    3.1
ELEMENTS:              %i
DATE:       %s
CHANNELS:           %i
ROIS:        %i %i %i %i
REAL_TIME:   1.0 1.0 1.0 1.0
LIVE_TIME:   1.0 1.0 1.0 1.0
CAL_OFFSET:  %15.8e %15.8e %15.8e %15.8e
CAL_SLOPE:   %15.8e %15.8e %15.8e %15.8e
CAL_QUAD:    %15.8e %15.8e %15.8e %15.8e
TWO_THETA:   10.0000000 10.0000000 10.0000000 10.0000000"""


        hout = [ndet, time.ctime(atime),n_energies, nrois, nrois, nrois, nrois]
        hout.extend( header['CAL_OFFSET'])
        hout.extend( header['CAL_SLOPE'])
        hout.extend( header['CAL_QUAD'])

        rout = []
        for i,r in enumerate(allrois):
            rout.append(roi_template % (i, r[0][1],r[1][1],r[2][1],r[3][1],
                                        i, r[0][2],r[1][2],r[2][2],r[3][2],
                                        i, r[0][0],r[1][0],r[2][0],r[3][0]))


        obuff ="%s\n%s" % (xrf_header % tuple(hout), '\n'.join(rout))
        
        self.xrf_header = obuff
        # print self.xrf_header
        # dir = prefix
        self.xrf_energies = []
        x_en = numpy.arange(n_energies)
        for i in range(ndet):
            off   = header['CAL_OFFSET'][i]
            slope = header['CAL_SLOPE'][i]
            quad  = header['CAL_SLOPE'][i]            
            self.xrf_energies.append(off + x_en * (slope + x_en * quad))

        self.xrf_energies = numpy.array(self.xrf_energies)

        self.xrf_dict = {}
        processing = True
        iyold = 1
        ix    = 0
        t0 = time.time()

        lines = inpf.readlines()
        n_print = 100
        for il, line in enumerate(lines):
            try:
                dat = [int(i) for i in line[:-1].split()]
                ix  = dat.pop(0)
                iy  = dat.pop(0)
                if iy != iyold:
                    iyold = iy

                self.xrf_dict['%i/%i' % (ix,iy)] =dat
                show_progress = self.progress
                self.progress = self.my_progress
                if (il % n_print) == 0: self.PrintMessage('. ')
                self.progress = show_progress
            except KeyboardInterrupt:
                return -3
        xrf_shape =  (n_xin, ndet, n_energies)
        if self.dimension == 2:
            xrf_shape =  (n_yin, n_xin, ndet, n_energies)            
            
        self.xrf_data = numpy.zeros(xrf_shape)
        if self.dimension == 2:
            for iy in range(n_yin):
                for ix in range(n_xin):
                    key = '%i/%i' % (ix+1,iy+1)
                    d = numpy.array(self.xrf_dict[key])
                    d.shape = (ndet, n_energies)
                    self.xrf_data[iy,ix,:,:] = d
        else:
            for ix in range(n_xin):
                key = '%i/%i' % (ix+1,iy)
                d = numpy.array(self.xrf_dict[key])
                d.shape = (ndet, n_energies)
                self.xrf_data[ix,:,:] = d
            
        self.xrf_dict = None
        # print 'XRF DATA  ',  iy, self.xrf_data.shape
        # print self.xrf_data[0,0,:,:]
        inpf.close()
        

    def get_detector_list(self,name=None,index=None,use_orig=None):
        l = []
        if name is not None:
            idet = self.match_detector_name(name)
            for i in range(len(m)):
                if (idet == m[i]):
                    l.append(i)
        return l        

    def set_detector_list(self,name=None,list=[]):
        " reset list of detectors for sum"
        i1 = self.match_detector_name(name)
        tmp_list = []
        for i,det in enumerate(self.det_names):
            nam,pv = det
            l  = self.get_detector_list(nam)
            if (i == i1):  l = list
            tmp_list.append(l)
            
        self.sums_list = []
        for i in range(self.ndetectors): self.sums_list.append(-1)
        for i in range(len(self.det_names)):
            for k in tmp_list[i]: self.sums_list[k] = i

        # re-make sums from detector lists
        # note use of copy.deepcopy()!!
        self.sums    = []
        for i in range(len(self.det_names)):
            l = tmp_list[i]
            if (len(l) > 0):
                t = self.det[l[0]]
                for j in range(1,len(l)):
                    t = t + self.det[l[j]]
            self.sums.append(copy.deepcopy(t))
        self.sums = numpy.array(self.sums)



if (__name__ == '__main__'):
    import sys
    u = escan_data(sys.argv[1])
    # print u.pv_list

    print 'info  : ', u.info
    
    print '== positioners'
    print u.pos_names
    print '== detectors'
    print u.det_names
    print '== sums'
    print u.sums_names
    print u.sums_list

    print 'Pos = ', u.pos.shape
    print 'Det = ', u.det.shape
#     # 
#     #     print u.det[3]
#     #     print u.sums[1]
#     #     print u.pos[0]
#     #     #a
    print 'X  = ', len(u.x)
    print 'Y  = ', u.y
    if u.has_fullxrf:
        print 'Full XRF Spectra: ', u.xrf_energies.shape

    
    # print u.match_detector_name('ca')
    #  
    # 
#     print u.get_data('ca',icr_correct=False)
#     print u.get_data('ca',icr_correct=True)

#      print u.det[1,:20]
#     print u.det_corr[1,:20]
    
