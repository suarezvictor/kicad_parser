#!/usr/bin/env python3

#schematics_file = "../YuzukiNezhaD1s_2024_easyedaexport/YuzukiNezha D1s - RISC-V Linux 2024.kicad_sch"
schematics_file = "/home/vsuarez/SCRATCH/victor_gpu_board/KiCad_files/YuzukiNezha D1s RISC-V Linux/YuzukiNezha D1s RISC-V Linux.kicad_sch"
schematics_file_out = schematics_file + ".out"

BOM_file = "Yuzuki-fix.csv"
designator_tag = "Designator"
footprint_tag = "Footprint"
overwrite_props = True

import csv
import sys
import re
from sexp_parser.sexp_parser import *

footprints = {}
footprints_direct_db = {
 "WSON-8_L8.0-W6.10-P1.27-BL-EP": "Package_SON:WSON-8-1EP_8x6mm_P1.27mm_EP3.4x4.3mm",
 "WQFN-20_L3.0-W3.0-P0.40-BL-EP1.7": "Package_DFN_QFN:WQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm",
 "IND-SMD_L2.0-W1.6": "Inductor_SMD:L_Cenker_CKCS201610"
}

def footprint_equivalence(designator, v):
  global footprints
  prefix = designator[0]
  if v in footprints_direct_db:
    return footprints_direct_db[v]
  if v in footprints:
    return footprints[prefix+v]

  inches = v
  inch2metric = {"0402": "1005", "0603": "1608" }
  #Capacitor_SMD:C_0402_1005Metric
  component_types = {"C":"Capacitor_SMD:C_", "R": "Resistor_SMD:R_"}
  if not inches in inch2metric or not prefix in component_types:
    return v
  metric = inch2metric[inches]
  f = component_types[prefix] + inches + "_" + metric + "Metric"
  footprints[prefix+v] = f
  return f

BOM = {}
with open(BOM_file, mode='r', encoding='utf-8') as file:
  csv_reader = csv.reader(file)
 
  header = next(csv_reader, None)
  #print("header", header)
  assert(designator_tag.upper() in [h.upper() for h in header])
  designator_tag = [h for h in header if designator_tag.upper() == h.upper()][0]

  for row in csv_reader:
    row_dict = {k: v for k, v in zip(header, row)}
    #print(row_dict)
    designators = row_dict[designator_tag].split(",")
    for designator in designators:
      assert(designator not in BOM) #check duplicates
      v = {k: v for k, v in row_dict.items() if k != designator_tag and v != ""}
      BOM[designator] = v

"""
for designator, v in BOM.items():
  for attr, value in v.items():
    if attr.upper() == footprint_tag.upper():
      value = footprint_lookup(designator, value)
    print(designator, attr+":", value)
"""


with open(schematics_file, 'r') as f:
  sch = SexpParser(parseSexp(f.read(), None))
  #exportSexp(sch, schematics_file_in, indent="\t")

errors_count = 0
warnings_count = 0

for sym in sch.symbol:
  #exportSexp(sym, sys.stdout)
  props = {p[0]: p[1] for p in sym.property}
  props_dict = {p[0]: p for p in sym.property}
  if not '"Reference"' in props or not '"Value"' in props:
    print("WARNING: no Reference or Value in ", props)
    continue
  reference = props['"Reference"']
  assert(reference[0]=='"' and reference[-1]=='"')
  reference = reference[1:-1]
  value = props['"Value"']
  assert(value[0]=='"' and value[-1]=='"')
  value = value[1:-1]
  

  if reference in BOM:
    component = BOM[reference]
    comment = component["Comment"]
    del component["Comment"]
    if value != comment:
      print("\033[91mERROR\033[0m: Kicad Value field and EasyEDA comment doesn't match for reference", reference, value, "!=", comment)
      errors_count += 1
    for k, v in component.items():
      if k == "Footprint":
        v = footprint_equivalence(reference, v)
      k = '"'+k+'"'
      v = '"'+v+'"'
      if not k in props:
        u = [k, v]
        dp = props_dict['"Footprint"']
        for x in dp: #copy attributes
          if isinstance(dp[x], list):
            u += [Sexp(x, dp[x])]
          if isinstance(dp[x], Sexp):
            u += [dp[x]]
        s = Sexp("property", u)
        print("\033[92mINFO\033[0m: added field to", reference, k, v)
        sym.property._append(s)
      elif overwrite_props or props[k] == '""': #update
        for p in sym.property:
         if p[0] == k:
           p._value[1] = v
        print("\033[92mINFO\033[0m: updated field to", reference, k, v)
        

exportSexp(sch, schematics_file_out, indent="\t")

print("\nResults:", errors_count, "errors,", warnings_count, "warnings")
exit(errors_count > 0)

