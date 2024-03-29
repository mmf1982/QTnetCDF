'''
function to load MFC files
'''
import struct
import numpy as np
import os
import glob
import pandas as pd
# import astropy.coordinates
import matplotlib.pyplot as plt
from add_interactivity import add_interactivity as ai

MFC_fields = ["version", "no_chan", "specpoint", "specname",
              "site_name",
              "spectro_name", "device_name", "first_line", "elevation", 
              "later", "someFlag", "date", "lowLim", 
              "upLim", "plot_low_lim", "plot_up_lim", 
              "act_chno", "number_scans", "integration_time", 
              "latitude", "longitude",
              "peak_number", "band_number", "min_spectrum", 
              "max_spectrum", "y_scale", "y_offset", 
              "wavelength1", "average", "disp1", "disp2", 
              "disp3", "opt_dens", "mode", "smooth", 
              "deg_reg", "Null", "Ref", "filename", 
              "backgrnd"] +    ["x"+str(i) for i in range(40)] + [
              "p_comment", "reg_no", "something", "something_else"]

MFC_headerFmt = "=20si4s20s20s20s20s80sf72si28s6i3f2i10fiii8s8s8s8s40i4pi4p4p"
MFC_headerLen = struct.calcsize(MFC_headerFmt)
MFC_headerUnpack = struct.Struct(MFC_headerFmt).unpack_from


'''
  char      version[20];           //     version number (not of interest)
  int       no_chan;               // !!! number of channels - 1 (usually 1023)
  char p_spec_32bit[4];            // 32-bit pointer used by DOASIS at runtime (?).
  char      specname[20];          //     optional name of the spectrum
  char      site[20];              //     name of measurement site
  char      spectroname[20];       //     name of spectrograph
  char      scan_dev[20];          //     name of scan device, e.g. PDA
  char      first_line[80];
  float     elevation;             //     elevation viewing angle
  char      spaeter[72];
  int       ty;                    //     spectrum flags, can be used to distinguish between
                                   //     different types of spectrum (e.g. straylight,
                                   //     offset, dark current...
  char      dateAndTime[28];
//  char     date[9];              // !!! date of measurement
//  char     start_time[9];        // !!! start time of measurement
//  char     stop_time[9];         // !!! stop time of measurement
//  char     dummy;
  int       low_lim;
  int       up_lim;
  int       plot_low_lim;
  int       plot_up_lim;
  int       act_chno;
  int       noscans;               // !!! number of scans added in this spectrum
  float     int_time;              // !!! integration time in seconds
  float     latitude;              //     latitude of measurement site
  float     longitude;             //     longitude of measurement site
  int       no_peaks;
  int       no_bands;
  float     min_y;                 //     minmum of spectrum
  float     max_y;                 //     maximum of spectrum
  float     y_scale;
  float     offset_Scale;
  float     wavelength1;           // !!! wavelength of channel 0
  float     average;               //     average signal of spectrum
  float     dispersion[3];         // !!! dispersion given as a polynome:
                                   //     wavelength=wavelength1 + dispersion[0]*C + dispersion[1]*C^2
                                   //                            + dispersion[2]*C^3;   C: channel number
                                   //                              (0..1023)
  float     opt_dens;
  TOldFlags OldFlags;
  char      FileName[8];           //     filename of spectrum
  char      backgrnd[8];
  int       gap_list[40];
  char      p_comment_32bit[4];
  int       reg_no;
  char p_prev_32bit[4], p_next_32bit[4];   //  2 32-bit pointers, presumably used by DOASIS at runtime
 }
 
          Format  C Type          Python type         Standard size  (byte)}     \n
         ======  ==============  ==================  ======================
         x       pad             byte                no value                   \n
         c       char            string of length 1  1                          \n
         b       signed char     integer             1                          \n
         B       unsigned char   integer             1                          \n
         ?       _Bool           bool                1                          \n
         h       short           integer             2                          \n
         H       unsigned short  integer             2                          \n
         i       int             integer             4                          \n
         I       unsigned int    integer             4                          \n
         l       long            integer             4                          \n
         L       unsigned long   integer             4                          \n
         q       long long       integer             8                          \n
         Q       unsigned long   long  integer       8                          \n
         f       float           float               4                          \n
         d       double          float               8                          \n
         s       char[]          string                                         \n
         p       char[]          string                                         \n
'''

def get_data(speFile, decoding="ISO 8859-15"):
    def extract_correct_info_from_header(header):
        for k in header:
            if isinstance(header[k], bytes):
                try:
                    header[k] = header[k].decode(encoding=decoding).replace("\x00"," ")
                except Exception as ex:
                    print(k, ex)
                    import pdb
                    pdb.set_trace()
        try:
            aim_tea, actual_tea, taa = [float(gg.replace("\x00"," ")) for gg in header["specname"].split()]
        except:
            print("no tea, probably dark or off")
            return header, False
        header["telescope_elevation_aim"] = aim_tea
        header["telescope_elevation_real"] = actual_tea
        header["telescope_azimuth_angle"] = taa
        mdate, starttime, stoptime, *rest = header["date"].split()
        header["startdate"] = pd.to_datetime(mdate + " " + starttime, format="%d.%m.%y %H:%M:%S")
        header["stopdate"] = pd.to_datetime(mdate + " " + stoptime,    format="%d.%m.%y %H:%M:%S")
        return header, True
    f = open(speFile,"rb")
    bytesPacked = f.read(MFC_headerLen)
    bytesUnpacked = MFC_headerUnpack(bytesPacked)
    header = dict(zip(MFC_fields, bytesUnpacked))
    header, ok = extract_correct_info_from_header(header)
    spectraSize = header["no_chan"] + 1
    spectrum = np.array(
            np.reshape(
                np.fromfile(f,dtype=np.float32,count=int(spectraSize)),(int(spectraSize),),order='F'),dtype=np.float32)
    if ok:
        return {"header": header, "spectrum": spectrum}, True
    else:
        return {"header": header, "spectrum": spectrum}, False

def read_all(mpath):
    mlist = glob.glob(mpath+"/U*")
    mlist.sort()
    md = {}
    useidx = 0
    done = False
    otherspec = []
    otherheader = {}
    for idx, m in enumerate(mlist):
        m = str(m)
        temp, normal = get_data(m)
        if not normal and not done:
            useidx = useidx +1
        if normal:
            if idx == useidx:
                spect = []
                hdr = {k: [] for k in temp["header"]}
            for k in temp["header"]:
                hdr[k].append(temp["header"][k])
            spect.append(temp["spectrum"])
        else:
            if len(otherspec) == 0:
                otherheader = {k: [] for k in temp["header"]}
            for k in temp["header"]:
                otherheader[k].append(temp["header"][k])
            otherspec.append(temp["spectrum"])
    for k in hdr:
        hdr[k] = np.array(hdr[k])
    for k in otherheader:
        otherheader[k] = np.array(otherheader[k])
    md["header"] = hdr
    md["other_header"] = otherheader
    # check for shorter spectra
    speclen = int(np.ceil(np.median(md["header"]["no_chan"])))
    midx = md["header"]["no_chan"] == speclen
    for k in hdr:
        md["header"][k] = md["header"][k][midx]
    spect = np.array(np.array(spect)[midx])
    print("number of measurements that are too short:",
          sum(~midx), np.arange(len(midx))[~midx])
    md["spectrum"] = spect
    # check for shorter spectra
    if len(md["other_header"]) > 0:
        speclen = int(np.ceil(np.median(md["other_header"]["no_chan"])))
        midx = md["other_header"]["no_chan"] == speclen
        for k in otherheader:
            md["other_header"][k] = md["other_header"][k][midx]
        otherspec = np.array(np.array(otherspec)[midx])
        print("number of measurements that are too short:",
            sum(~midx), np.arange(len(midx))[~midx])
        md["other_spectrum"] = otherspec
    return md
