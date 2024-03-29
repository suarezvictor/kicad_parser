file_path = "/home/vsuarez/Downloads/Project_YuzukiNezha D1s - RISC-V Linux_2022-01-07_23-15-16/1-Schematic_YuzukiNezha D1s - RISC-V Linux.json"

relevant_attrs = {"Manufacturer":"MFG", "Manufacturer Part":"MPN", "package":"Footprint"}
relevant_suppliers = {"LCSC":"LCSC Part Number"}
supplier_part_tag = "Supplier Part"
supplier_tag = "Supplier"
BOM_columns_set = "Comment,Designator,Footprint,LCSC Part Number"

import json
import re
from types import SimpleNamespace

def read_json(file_path):
  with open(file_path, 'r') as file:
    data = json.load(file, object_hook=lambda d: SimpleNamespace(**d))
    return data


footprints = {}
def footprint_lookup(v):
  global footprints
  if v in footprints:
    return footprints[v]

  match = re.match(r"([CR])(\d{4})[- ]?NSK", v)
  if not match:
    return v
    
  return match.group(2)
  """
  prefix = match.group(1)
  inches = match.group(2)
  inch2metric = {"0402": "1005", "0603": "1608" }
  #Capacitor_SMD:C_0402_1005Metric
  component_types = {"C":"Capacitor_SMD:C_", "R": "Resistor_SMD:R_"}
  if not inches in inch2metric or prefix not in component_types:
    return v
  metric = inch2metric[inches]
  f = component_types[prefix] + inches + "_" + metric + "Metric"
  footprints[v] = f
  return f
  """
    

data = read_json(file_path)
#print(json.dumps(data, indent=4))  # Dumping the contents with indentation for better readability
#obj = JsonObject(data)

sch = {"LIB":{}}
for sheet in data.schematics:
  #print("Processing sheet:", sheet.title)
  for symbolstr in sheet.dataStr.shape:
    props = symbolstr.split("~")
    #print("props", props)
    #https://github.com/KiCad/kicad-source-mirror/blob/e347300593815d1b3a7317b30e600caff5ef570f/eeschema/sch_io/easyeda/sch_easyeda_parser.cpp#L384
    if props[0] == "LIB":
      #coord = props[1], props[2]
      attr = props[3]
      attrs = attr.split("`")
      component = {}
      component_attrs = component["attrs"] = {}

      spicePre = None
      mfg = None
      mpn = None
      supplier = None
      supplier_part = None
      designator = None


      #other_tags = [a.upper() for a in relevant_suppliers.values()] + [supplier_tag.upper()]
      k_attrs = [a.upper() for a in relevant_attrs] #+ other_tags
      attr_dict = {}
      i = 0
      while i < len(attrs)-1:
        k = attrs[i]
        v = attrs[i+1]
        i += 2
        if k == "package":
          v = footprint_lookup(v)

        if k.upper() in k_attrs and v != "":
          component_attrs[relevant_attrs[k]] = v
        if k == "spicePre":
          spicePre = v
        if k.upper() == supplier_tag.upper():
          supplier = v if v != "" else None
        if k.upper() == supplier_part_tag.upper():
          supplier_part = v if v != "" else None

      if supplier is not None and supplier_part is not None:
        component_attrs[supplier] = supplier_part
      
      comments = component["comments"] = []
      value = None
      i = 3;
      while i < len(props):
        if props[i] == "comment":
          comment = props[i+1]
          comments += [comment]
          if designator is None and spicePre is not None and comment.startswith(spicePre):
            designator = comment
          if value is None:
            value = comment
          i += 1
        i += 1
      
      if value is not None:
        component_attrs["Comment"] = value
        
      if designator is not None and component_attrs:
        sch["LIB"][designator] = component_attrs
        #print("component", comments, "attrs", component_attrs)

BOM = {}
BOM_columns = BOM_columns_set.split(",")
for k, v in sch["LIB"].items():
  #supplier_column = relevant_suppliers[supplier]
  attr = {}
  for kk, vv in v.items():
    if kk in relevant_suppliers:
      kk = relevant_suppliers[kk]
    attr[kk] = vv
    if kk not in BOM_columns:
      BOM_columns += [kk]
  #print(k, "=>", attr)
  designator = k
  k = tuple(attr.items())
  if not k in BOM:
    BOM[k] = designator
  else:
    BOM[k] = BOM[k] + "," + designator

print(",".join(BOM_columns))
for k, v in BOM.items():
  line = []
  mp = dict(k)
  for c in BOM_columns:
    if c == "Designator":
      line += ['"'+v+'"']
    else:
      line += ['"'+mp[c]+'"'] if c in mp else ['""']
  print(",".join(line))

