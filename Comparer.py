from pandas.util.testing import assert_frame_equal
import pandas
import sys
import numpy as np

if len(sys.argv) < 3 :
    print ("Please pass 2 files to compare")
    print ("Format : Comparer.py file1 file2")
    sys.exit(2)

autocsv = pandas.read_csv(sys.argv[1],dtype={'datetime': np.string_, 'Stall Count': np.str,'Calls per Minute': np.string_, 'Sum of Calls per Minute': np.string_, 'Number of Very Slow Calls': np.string_,
                                              'Number of Slow Calls': np.string_, 'Average Response Time (ms)': np.string_ , 'Sum of Average Response Time (ms)': np.string_ ,
                                              'Errors per Minute': np.string_ ,'Sum of Errors per Minute': np.string_})

manualcsv = pandas.read_csv(sys.argv[2])

old_names = ['Date', 'Value:BTM|Application Summary|Stall Count', 'Value:BTM|Application Summary|Number of Very Slow Calls', 'Value:BTM|Application Summary|Calls per Minute', 'Sum:BTM|Application Summary|Calls per Minute',
             'Value:BTM|Application Summary|Number of Slow Calls', 'Value:BTM|Application Summary|Average Response Time (ms)', 'Sum:BTM|Application Summary|Average Response Time (ms)',
             'Value:BTM | Application Summary | Errors per Minute', 'Sum:BTM | Application Summary | Errors per Minute']
new_names = ['datetime','Stall Count','Number of Very Slow Calls','Calls per Minute','Sum of Calls per Minute','Number of Slow Calls',
             'Average Response Time (ms)','Sum of Average Response Time (ms)' ,'Errors per Minute' ,'Sum of Errors per Minute']
manualcsv.rename(columns=dict(zip(old_names, new_names)), inplace=True)

manualcsv = manualcsv.drop('Sum:BTM|Application Summary|Number of Slow Calls', 1)
manualcsv = manualcsv.drop('Sum:BTM|Application Summary|Number of Very Slow Calls', 1)
manualcsv = manualcsv.drop('Sum:BTM|Application Summary|Stall Count', 1)

autocsv['Sum of Average Response Time (ms)'].fillna('--',inplace=True)

autocsv = autocsv.sort_index(axis=1)
manualcsv = manualcsv.sort_index(axis=1)

try:
    assert_frame_equal(autocsv, manualcsv)
    print ("Success")
except:  # appeantly AssertionError doesn't catch all
    print ("Failed")