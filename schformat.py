#!/usr/bin/env python3

#schematics_file = "../YuzukiNezhaD1s_2024_easyedaexport/YuzukiNezha D1s - RISC-V Linux 2024.kicad_sch"
schematics_file = "/home/vsuarez/SCRATCH/victor_gpu_board/KiCad_files/YuzukiNezha D1s RISC-V Linux/YuzukiNezha D1s RISC-V Linux.kicad_sch"

from sexp_parser.sexp_parser import *


with open(schematics_file, 'r') as f:
  sch = SexpParser(parseSexp(f.read(), None))

exportSexp(sch, schematics_file, indent="\t")

