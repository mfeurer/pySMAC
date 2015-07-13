import json
import functools
import re
import operator

import numpy as np



def json_parse(fileobj, decoder=json.JSONDecoder(), buffersize=2048):
    """ Small function to parse a file containing JSON objects separated by a new line. This format is used in the live-rundata-xx.json files produces by SMAC
    
    taken from http://stackoverflow.com/questions/21708192/how-do-i-use-the-json-module-to-read-in-one-json-object-at-a-time/21709058#21709058
    """
    buffer = ''
    for chunk in iter(functools.partial(fileobj.read, buffersize), ''):
        buffer += chunk
        buffer = buffer.strip(' \n')
        while buffer:
            try:
                result, index = decoder.raw_decode(buffer)
                yield result
                buffer = buffer[index:]
            except ValueError:
                # Not enough data to decode, read more
                break


# Reads a run_results file from a state-run folder and stores in a numpy array
# The run results are the only non numeric column here. They are mapped
# according to:
# SAT -----> 1
# UNSAT ---> 0
# TIMEOUT -> -1
# ELSE ----> -2
def read_runs_and_results_file(fn):
    """ Converting a runs_and_results file into a numpy array.
    
    Almost all entries in a runs_and_results file are numeric to begin with.
    Only the 14th column contains the status which is encoded as ints by SAT = 1,
    UNSAT = 0, TIMEOUT = -1, everything else = -2.
    
    .. todo::
       explain every column
    
    :returns: numpy_array(dtype = double) -- the data
    """
    # to convert everything into floats, the run result needs to be mapped
    def map_run_result(res):
         if b'TIMEOUT' in res:  return(0)
         if b'UNSAT' in res:    return(1) # note UNSAT before SAT, b/c UNSAT contains SAT!
         if b'SAT' in res:      return(2)
         return(-1)    # covers ABORT, CRASHED, but that shouldn't happen
    
    return(np.loadtxt(fn, skiprows=1, delimiter=',',
        usecols = list(range(1,14))+[15], # skip empty 'algorithm run data' column
        converters={13:map_run_result}, ndmin=2))


# reads a paramstring file from a state-run folder
# The returned list contains dictionaries with
# 'parameter_name': 'value_as_string' pairs
def read_paramstrings_file(fn):
    """ Function to read a paramstring file.
    Every line in this file corresponds to a full configuration. Everything is
    stored as strings and without knowledge about the pcs, converting that into
    any other type would involve guessing, which we shall not do here.
    
    :param fn: the name of the paramstring file
    :type fn: str
    :returns: dict -- with key-value pairs 'parameter name'-'value as string'
    
    """
    param_dict_list = []
    with open(fn,'r') as fh:
        for line in fh.readlines():
            # remove run id and single quotes
            line = line[line.find(':')+1:].replace("'","")
            pairs = [s.strip().split("=") for s in line.split(',')]
            param_dict_list.append({k:v for [k, v] in pairs})
    return(param_dict_list)

 
# Reads a validationCallString file and returns a list of dictonaries
# Each dictionary consists of parameter_name: value_as_string entries
def read_validationCallStrings_file(fn):
    """Reads a validationCallString file into a list of dictionaries.
    
    :returns: list of dicts -- each dictionary contains 'parameter name' and 'parameter value as string' key-value pairs
    """
    param_dict_list = []
    with open(fn,'r') as fh:
        for line in fh.readlines()[1:]: # skip header line
            config_string = line.split(",")[1].strip('"')
            config_string = config_string.split(' ')
            tmp_dict = {}
            for i in range(0,len(config_string),2):
                tmp_dict[config_string[i].lstrip('-')] = config_string[i+1].strip("'")
            param_dict_list.append(tmp_dict)
    return(param_dict_list)


def read_validationObjectiveMatrix_file(fn):
    """
    .. todo::
        add documentation for this one
    """
    values = {}
    
    with open(fn,'r') as fh:
        header = fh.readline().split(",")
        num_configs = len(header)-2
        re_string = '\w?,\w?'.join(['"id\_(\d*)"', '"(\d*)"']  + ['"([0-9.]*)"']*num_configs)
        for line in fh.readlines():
            match = (re.match(re_string, line))
            values[int(match.group(1))] = list(map(float,list(map(match.group, list(range(3,3+num_configs))))))
    return(values)


def read_instances_file(fn):
    """
    Reads the instance names from an instace file
    
    :returns: list -- each element is a list where the first element is the instance name followed by additional information for the specific instance.
    """
    with open(fn,'r') as fh:
        instance_names = fh.readlines()
    return([s.strip().split() for s in instance_names])


def read_instance_features_file(fn):
    """Function to read a instance_feature file.
    
    :returns: tuple -- first entry is a list of the feature names, second one is a dict with 'instance name' 'numpy array containing the features'
    """
    instances = {}
    with open(fn,'r') as fh:
        lines = fh.readlines()
        for line in lines[1:]:
            tmp = line.strip().split(",")
            instances[tmp[0]] = np.array(join(tmp[1:]),dtype=np.double)
    return(lines[0].split(",")[1:], instances)
