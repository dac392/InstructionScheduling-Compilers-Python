from Schedule import *
import concurrent.futures

from os import listdir
from os.path import isfile, join
import os



BENCH_PATH = "../benchmarks/"
modes = ['-a','-b','-c']

benchmarks_a = [f for f in listdir(BENCH_PATH) if isfile(join(BENCH_PATH, f))]
#print(f"benchmark files: {benchmarks}")
#print(benchmarks)
benchmarks = [f for f in benchmarks_a if "bench" in f]
print(f"benchmarks: {benchmarks}")
with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(testing_function, benchmarks)

testing_files = [f for f in listdir("./results/") if isfile(join("./results",f))]
for file in testing_files:
        os.system(f"../ILOC_Simulator/sim < ./results/{file} > ./iloc_results/{file}")
print("Done")
