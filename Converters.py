"""Module to convert different file formats to be used in NetCDF4viewer. Currently only hdf4 implemented"""
import pyhdf
import pyhdf.SD
import pyhdf.HDF
import pyhdf.VS
import pyhdf.V
import numpy
from pyhdf.error import HDF4Error
from collections import OrderedDict
import pandas

try:
    from . import MFC
except:
    try:
        import MFC
    except:
        try:
            import sys
            sys.path.append("/ae/projects4/FRM4DOAS/programs/tags/validation_02.0/python/")
            import tools.MFC_Format as MFC
        except:
            pass

HDFTYPE = {pyhdf.HDF.HC.DFTAG_NDG: "HDF SDS",
           pyhdf.HDF.HC.DFTAG_VH: "HDF Vdata",
           pyhdf.HDF.HC.DFTAG_VG: "HDF Group"}

DATATYPE = {pyhdf.SD.SDC().COMP_SZIP_RAW: "complex",
            pyhdf.SD.SDC().COMP_SZIP_NN: "complex",
            pyhdf.SD.SDC().COMP_SZIP_EC: "complex",
            pyhdf.SD.SDC().COMP_SZIP: "complex",
            pyhdf.SD.SDC().INT8: "int8",
            pyhdf.SD.SDC().INT16: "int16,",
            pyhdf.SD.SDC().INT32: "int32",
            pyhdf.SD.SDC().UINT8: "uint8",
            pyhdf.SD.SDC().UINT16: "uint16",
            pyhdf.SD.SDC().UINT32: "unint32",
            pyhdf.SD.SDC().FLOAT32: "float32",
            pyhdf.SD.SDC().FLOAT64: "float64",
            pyhdf.SD.SDC().CHAR: "char",
            pyhdf.SD.SDC().CHAR8: "char8",
            pyhdf.SD.SDC().UNLIMITED: "unlimited",
            pyhdf.SD.SDC().UCHAR: "uchar",
            pyhdf.SD.SDC().UCHAR8: "uchar8",
            }


class Table(numpy.ma.core.MaskedArray):
    """
    numpy array with header and attribute
    """

    def __new__(cls, content, header, attr):
        try:
            mval = numpy.ma.masked_equal(content, attr["_FillValue"]).view(cls)
        except:
            mval = numpy.ma.asarray(content).view(cls)
        mval.header = header
        mval.attributes = attr
        return mval


class Text(str):
    """this enables to attach data to a string"""

    def __new__(cls, content):
        return super(Text, cls).__new__(cls, content.name)

    def __init__(self, content):
        super().__init__()
        self.data = content

    def change_data(self, mdata):
        self.data = mdata


class MyDict(dict):
    """
    this allows to put attributes to a dictionary
    """

    def __new__(cls):
        return super(MyDict, cls).__new__(cls)

    def __init__(self):
        super().__init__()
        self.attributes = {}


class Hdf4Object:
    """Class to hold the content of an hdf4 file """
    def __init__(self, filename: str):
        self.done = []
        self.sd = pyhdf.SD.SD(filename)
        self.hdf = pyhdf.HDF.HDF(filename)
        self.vs = self.hdf.vstart()
        self.v = self.hdf.vgstart()
        self.allv_ids = set(self.all_v_ids(-1, [])[1])
        allvs_ids = [entr[2] for entr in self.vs.vdatainfo(0)]
        self.ref_for_dims = self.find_dims()
        self.ref_for_attrs = self.find_ref_v_for_attr()
        self.struct = self.get_struct()
        for key in self.struct:
            try:
                md = self.struct[key].data
                key.change_data(Representative(md.ref(), pyhdf.HDF.HC.DFTAG_NDG, self))
                self.struct[key] = Representative(md.ref(), pyhdf.HDF.HC.DFTAG_NDG, self)
            except:
                pass
        self.struct.attributes = self.sd.attributes()
        self.add_vs_to_main(allvs_ids)

    def find_ref_v_for_attr(self):
        no_attr = [entr[2] for entr in self.vs.vdatainfo(0)]
        w_attr = [entr[2] for entr in self.vs.vdatainfo(1)]
        attr_refs = set(w_attr).difference(set(no_attr))
        return attr_refs

    def add_vs_to_main(self, vs_list_initial):
        """Adds the vdata which is not dimension and not attribute to the main level"""
        mlist = list(set(vs_list_initial).difference(set(self.ref_for_dims)))
        for ref in mlist:
            info = self.vs.attach(ref).inquire()  # len, ?, header, bytes, name
            if len(info[-1]) > 0 and info[-1][0] != "_":
                mobject = Representative(ref, pyhdf.HDF.HC.DFTAG_VH, self)
                name = Text(mobject)
                self.struct[name] = mobject
        return

    @property
    def list_all_dims(self):
        """
        get dimensions of a variable

        :return: dictionary containing all dimension names and values
        """
        mdict = {}
        for ref in self.ref_for_dims:
            md = self.vs.attach(ref)
            name = md.inquire()[4]
            value = md[:]
            mdict[name] = (value, ref)
        return mdict

    def find_dims(self):
        """
        find of all vdata those that define dimensions

        :return: list of reference numbers of vdata that are only dimension
        """
        allvdata = self.vs.vdatainfo(0)  # 0 is for not listing those that are used to list attribute values
        onlydim = [entr[2] for entr in allvdata if "DimVal" in entr[1]]
        return onlydim

    def all_v_ids(self, ref, refs):
        """Find all vgroups in file and with it all data within it. Only data missed this way are vdata on main level"""
        try:
            ref = self.v.getid(ref)
            refs.extend([ref])
            ref, refs = self.all_v_ids(ref, refs)
            return ref, refs
        except pyhdf.error.HDF4Error:
            try:
                ref = self.vs.next(ref)
                refs.extend([ref])
                ref, refs = self.all_v_ids(ref, refs)
            except pyhdf.error.HDF4Error:
                pass
            return ref, refs
        except RecursionError:
            return ref, refs

    def get_struct(self):
        """
        get the structure of the hdf4 file
        """
        _, allrefs = self.all_v_ids(-1, [])
        mydict = MyDict()
        skipkeys = []
        newallrefs = []
        for ref in allrefs:
            if ref not in skipkeys and ref not in self.ref_for_dims:
                name = Text(Representative(ref, pyhdf.HDF.HC.DFTAG_VG, self))
                mydict[name], to_extend = self.get_nested_struct(ref)
                skipkeys.extend(to_extend)
                newallrefs.append(ref)
        self.remove_fakedim(mydict)  # remove fakedims and empty dicts
        return mydict

    def detect_v_group_for_sd_var(self, vgrref, elements):
        sd_var = [el[1] for el in elements if el[0] == pyhdf.HDF.HC.DFTAG_NDG]
        if len(sd_var) == 1:
            attrs_sd = list(self.sd.select(self.sd.reftoindex(sd_var[0])).attributes().keys())
            vs_nrs = [el[1] for el in elements if el[0] == pyhdf.HDF.HC.DFTAG_VH]
            attrs_here = [self.vs.attach(el).inquire()[-1] for el in vs_nrs]
            attrs_here = [attr for attr in attrs_here if len(attr) > 0]
            if set(attrs_sd) == set(attrs_here) and sd_var[0] in self.done:
                return vgrref
            elif set(attrs_sd) == set(attrs_here):
                return sd_var
        return False

    def remove_fakedim(self, mydict):
        if isinstance(mydict, dict):
            keylist = list(mydict.keys())
            for key in keylist:
                if isinstance(mydict[key], dict):
                    if len(mydict[key]) == 0:
                        pass
                        _ = mydict.pop(key)
                    else:
                        self.remove_fakedim(mydict[key])
                else:
                    name = mydict[key].name
                    if name is not None and "fakeDim" in name:
                        _ = mydict.pop(key)

    def get_nested_struct(self, myref):
        gr = self.v.attach(myref)
        elements = gr.tagrefs()
        not_continue = self.detect_v_group_for_sd_var(myref, elements)
        mydict = MyDict()
        refsdone = [myref]
        if not_continue:
            if isinstance(not_continue, list):
                obj = Representative(not_continue[0], pyhdf.HDF.HC.DFTAG_NDG, self)
                name = Text(obj)
                mydict[name] = obj
                return obj, refsdone
            else:
                return mydict, refsdone
        for tag, ref in elements:
            if ref not in self.ref_for_dims and ref not in self.ref_for_attrs:
                try:
                    name = Text(Representative(ref, tag, self))
                    mydict[name], to_extend = self.get_nested_struct(ref)
                    refsdone.extend([ref])
                    refsdone.extend(to_extend)
                except:
                    myobj = Representative(ref, tag, self)
                    name = Text(myobj)
                    mydict[name] = myobj
                    refsdone.extend([ref])
                self.done.append(ref)
        return mydict, refsdone

    def close(self):
        self.sd.end()
        self.hdf.close()

class nd_with_name(numpy.ma.core.MaskedArray):
    def __new__(cls, input_array, name):
        '''
        Constructor of ndarray with name

        Parameters:
        -----------
        input_array: array like
            array that constitutes the LUT
        name: str
            name of variable
        Returns:
        --------
        obj: LUT object
        '''
        obj = numpy.ma.asarray(input_array).view(cls)
        obj.name = name
        obj.dimensions = ()
        #obj.mask = numpy.False
        return obj

class var_with_attr(numpy.ndarray):
    '''
    add the value as the units attribute
    '''
    def __new__(cls, data, name):
        obj = numpy.asarray(data).view(cls)
        obj.units = data
        return obj


class MFC_type(OrderedDict):
    def __new__(self, myfile):
        def makedictformat(temp):
            mdict = OrderedDict()
            mdict2 = OrderedDict()
            anyduplicated = False
            duplicatedtime = []
            def makedate(hd):
                datestring = (str(hd["da_year"]).zfill(4) + "-" +
                            str(hd["da_month"]).zfill(2) + "-" +
                            str(hd["da_day"]).zfill(2) + " " +
                            str(hd["start_ti_hour"]).zfill(2) + ":" +
                            str(hd["start_ti_min"]).zfill(2) + ":" +
                            str(hd["start_ti_sec"]).zfill(2))
                return datestring
            for mline in temp:
                mkey = makedate(mline.header)
                if mkey in mdict:
                    print(mkey, " duplicated, put in data2")
                    duplicatedtime.append(mkey)
                    anyduplicated = True
                    mdict2[mkey] = {key: var_with_attr(mline.header[key], key) for key in mline.header}
                    mdict2[mkey]["spectrum"] = nd_with_name(mline.spectrum, "spectrum")
                    mdict2[mkey]["spectrum_corrected"] = nd_with_name(mline.spectrumCorrected, "spectrum_corrected")
                    continue
                mdict[mkey] = {key: var_with_attr(mline.header[key], key) for key in mline.header}
                mdict[mkey]["spectrum"] = nd_with_name(mline.spectrum, "spectrum")
                mdict[mkey]["spectrum_corrected"] = nd_with_name(mline.spectrumCorrected, "spectrum_corrected")
            datearray = numpy.array([pandas.to_datetime(mkey, format="%Y-%m-%d %H:%M:%S") for mkey in  mdict.keys()])
            if anyduplicated:
                datearray2 = numpy.array([pandas.to_datetime(mkey, format="%Y-%m-%d %H:%M:%S") for mkey in  duplicatedtime])
            allheaderdict = {k: [] for k in temp[0].header}
            allheaderdict2 = {k: [] for k in temp[0].header}
            for idx, mkey in enumerate(mdict.keys()):
                try:
                    line = mdict[mkey]
                    for k in allheaderdict:
                        allheaderdict[k].append(line[k])
                except:
                    print(idx)
                    pdb.set_trace()
            for k in allheaderdict:
                allheaderdict[k] = nd_with_name(numpy.array(allheaderdict[k]), k)
            # for some reason all data is twice in the file
            if anyduplicated:
                for idx, mkey in enumerate(mdict2.keys()):
                    try:
                        line = mdict2[mkey]
                        for k in allheaderdict2:
                            allheaderdict2[k].append(line[k])
                    except:
                        print(idx)
                        pdb.set_trace()
                for k in allheaderdict2:
                    allheaderdict2[k] = nd_with_name(numpy.array(allheaderdict2[k]), k)
            # end for some reason data is twice in the file
            mdict["all_data"] = {
                "spectrum" : nd_with_name(
                    numpy.array([mdict[key]["spectrum"] for key in mdict]), "spectrum"),
                "spectrum_corrected": nd_with_name(
                    numpy.array([mdict[key]["spectrum_corrected"] for key in mdict]), "spectrum_corrected"),
                "datetime": nd_with_name(datearray, "datetime")
                }
            mdict["all_data"].update(allheaderdict)
            mdict["all_data"]["index"] = nd_with_name(numpy.arange(len(temp[0].spectrum)), "index")
            if anyduplicated:
                mdict["duplicated_data"] = {
                    "spectrum" : nd_with_name(
                        numpy.array([mdict2[key]["spectrum"] for key in mdict2]), "spectrum"),
                    "spectrum_corrected": nd_with_name(
                        numpy.array([mdict2[key]["spectrum_corrected"] for key in mdict2]), "spectrum_corrected"),
                    "datetime": nd_with_name(datearray2, "datetime")
                    }
                mdict["duplicated_data"].update(allheaderdict2)
                mdict["duplicated_data"]["index"] = nd_with_name(numpy.arange(len(temp[0].spectrum)), "index")
                mdict.move_to_end("duplicated_data", last=False)
            mdict.move_to_end("all_data", last=False)
            return mdict
        correctionFlag = 1
        averageFlag = 0
        try:
            temp = MFC.MFC_BIRA_ReadSpe(myfile, correctionFlag, averageFlag)
        except PermissionError:
            print("no permission granted")
            return "no permission granted"
        return OrderedDict(makedictformat(temp))

class Representative:
    def __init__(self, myref, mtype, myfile):
        self.myref = myref
        self.tag = mtype
        self.myfile = myfile

    def __getitem__(self, key):
        return self.data[key]

    def getstuff(self):
        header = None
        name = rank = dims = stype = nattrs = ""
        if self.tag == pyhdf.HDF.HC.DFTAG_VH:
            dims, rank, header, inbytes, name = (self.myfile.vs.attach(self.myref).inquire())
            if isinstance(self.data, Table):
                rank = self.data.data.ndim
                dims = self.data.data.shape
                header = self.data.header
        elif self.tag == pyhdf.HDF.HC.DFTAG_NDG:
            name, ndims, dims, stype, _ = (self.myfile.sd.select(self.myfile.sd.reftoindex(self.myref)).info())
            sdo = self.myfile.sd.select(self.myfile.sd.reftoindex(self.myref))
            nattrs = sdo.attributes()
            dims = [str(sdo.dimensions()[k]) for k in sdo.dimensions().keys()]
            stype = DATATYPE[stype]
            rank = len(dims)
        elif self.tag == pyhdf.HDF.HC.DFTAG_VG:
            name = self.myfile.v.attach(self.myref)._name
        if len(nattrs) == 0:
            try:
                nattrs = self.get_info[0]
            except:
                pass
        return name, rank, dims, stype, nattrs, header

    @property
    def get_info(self):
        try:
            attributes = self.data.attrinfo()
            otherinfo = self.data.inquire()
        except:
            try:
                attributes = self.data.attributes()
                otherinfo = self.data.info()
            except:
                try:
                    attributes = self.data.attrinfo()
                    otherinfo = None
                except:
                    attributes = {}
                    otherinfo = None
        return attributes, otherinfo

    def print_info(self):
        """
        Function to print the info on a variable and its attributes
        """
        print("info on " + self.name)
        print("-----------")
        for attr in self.attributes:
            print(attr + ": " + str(self.attributes[attr]))
        print("---")

    @property
    def name(self):
        name, rank, dims, stype, nattrs, header = self.getstuff()
        return name

    @property
    def ndim(self):
        name, rank, dims, stype, nattrs, header = self.getstuff()
        return rank

    @property
    def dims(self):
        name, rank, dims, stype, nattrs, header = self.getstuff()
        return dims

    @property
    def stype(self):
        name, rank, dims, stype, nattrs, header = self.getstuff()
        return stype

    @property
    def header(self):
        name, rank, dims, stype, nattrs, header = self.getstuff()
        return header

    def get_value(self):
        try:
            fillvalue = self.get_info[0]["FillValue"]
        except KeyError:
            try:
                fillvalue = self.get_info[0]["_FillValue"]
            except KeyError:
                try:
                    fillvalue = self.get_info[0]["VAR_FILL_VALUE"]
                except KeyError:
                    try:
                        fillvalue = self.get_info[0]["_fillvalue"]
                    except KeyError:
                        return numpy.ma.array(self.data[:])
        return numpy.ma.masked_equal(self.data[:], fillvalue)

    @property
    def data(self):
        if self.tag == pyhdf.HDF.HC.DFTAG_VG:
            data = self.myfile.v.attach(self.myref)
        elif self.tag == pyhdf.HDF.HC.DFTAG_VH:
            data = self.myfile.vs.attach(self.myref)
            header = data.inquire()[2]
            attributes = {}
            for head in header:
                attributes[head] = {key: data.field(head).attrinfo()[key][2] for key in data.field(head).attrinfo()} \
                    # data.field(head).attrinfo()
            attributes["general"] = {key: data.attrinfo()[key][2] for key in data.attrinfo()}  # data.attrinfo()
            fillvalue = None
            for k in attributes:
                if "fillvalue" in k.lower() or "fill_value" in k.lower():
                    fillvalue = data.mdata.attributes[key]
                    break
            attributes["_FillValue"] = fillvalue
            data = numpy.ma.masked_equal(data[:], fillvalue)
            data = Table(data[:], header, attributes)
        elif self.tag == pyhdf.HDF.HC.DFTAG_NDG:
            try:
                data = self.myfile.sd.select(self.myfile.sd.reftoindex(self.myref))
            except:
                print(self.myref, self.tag)
                data = None
        else:
            data = None
        return data

    @property
    def dimensions(self):
        try:
            dimensions = self.data.dimensions()
            return dimensions.keys()
        except AttributeError:
            return []

    @property
    def type(self):
        if self.tag == pyhdf.HDF.HC.DFTAG_VG:
            return "vgroup"
        elif self.tag == pyhdf.HDF.HC.DFTAG_VH:
            return "vdata"
        elif self.tag == pyhdf.HDF.HC.DFTAG_NDG:
            return "sd_dataset"

    @property
    def attributes(self):
        allattr = {}
        if self.tag == pyhdf.HDF.HC.DFTAG_VG:
            allattr = self.data.attrinfo()
            allattr = {key: allattr[key][2] for key in allattr}
        elif self.tag == pyhdf.HDF.HC.DFTAG_NDG:
            allattr = self.data.attributes()
        elif self.tag == pyhdf.HDF.HC.DFTAG_VH:
            try:
                allattr = self.data.attributes
            except:
                allattr = {}
        return allattr
