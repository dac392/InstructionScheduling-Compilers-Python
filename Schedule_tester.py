import Schedule.py
import concurrent.futures

from os import listdir
from os.path import isfile, join




BENCH_PATH = "../benchmarks/"
modes = ['-a','-b','-c']

benchmarks = [f for f in listdir(BENCH_PATH) if isfile(join(mypath, f))]
with concurrent.futures.ProcessPoolExcecutor() as executor:
	executor.map(testing_function, benchmarks)