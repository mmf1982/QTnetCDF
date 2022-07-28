from cftime import num2date, date2num

def check_for_time(mdata):
    mydata = mdata[:]
    try:
        unit = mdata.units
    except Exception as err:
        print(err)
        unit = None
    if "time" in mdata.name.lower():
        try:
            unit = mdata.units
            mydata = num2date(mydata, unit, only_use_cftime_datetimes=False)
        except:
            pass
    print("found unit is: ", unit)
    return mydata, unit

def convert_from_time(mdata):
    #unit = "hours since "+mdata[0].strftime("%Y-%m-%d %H:%M:%S")
    mdata.datavalue = date2num(mdata.datavalue, mdata.units)
    print("dtype:", mdata.datavalue.dtype)
    print("units:", mdata.units)
    return mdata
