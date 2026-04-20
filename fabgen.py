#see also https://yaqwsx.github.io/KiKit/latest/fabrication/jlcpcb/
#https://github.com/yaqwsx/KiKit/blob/master/kikit/fab/jlcpcb.py
#KiKit allows you to specify the origin and orientation correction of the position. The correction is specified by JLCPCB_CORRECTION field. The field value is a semicolon separated tuple: <X>; <Y>; <Rotation> with values in millimeters and degrees

#Rotations depending on packages:
#see https://github.com/bennymeg/JLC-Plugin-for-KiCad/blob/master/plugins/transformations.csv
#also cpl_rotations_db.csv

#db: https://github.com/cs2dsb/lcsc-scrape.rs/releases

#
part_tags = [] #Manufacturer part number tags
fab_tag="" #only set for JLCPCB or others that has a component database
manufacturer_tag = "MFG" #Manufacturer name tag

import sys
import os

if __name__ == "__main__":
  if len(sys.argv) < 2:
      print("ERROR: pass filename as argument")
      exit(1)

fname = sys.argv[1]
part_tags = ['MPN', 'MPN_ALT']; fab_tag = "LCSC Part Number"

from kicad_pcb import KicadPCB
pcb = KicadPCB.load(fname)

fab_format = "JLCPCB"
#fab_format = "Hitech PCB"
#fab_format = "PCBgogo"
#fab_format = "AllPCB"; fab_tag=""

#Hitech PĈB
#BOM format: ID, Designator, Name, Quantity, Manufacturer Part Number, Manufacturer
#POS: Designator, Comment, Layer "TopLayer/BottomLayer", Footprint, Center-X, Center-Y, Rotation, Description
#PCBgogo
#BOM: Quantity,Designator,Description,Value,Footprint,Manufacturer,Part Number
#POS: Designator, Comment, Layer "TopLayer/BottomLayer", Footprint, Center-X(mil), Center-Y(mil), Rotation, Description
#AllPCB
#BOM: Quantity,Designator,Description,Value,Footprint,Manufacturer,Part Number,[Buying link]
#POS: designators, X-coordinate, Y-coordinate, components angle


postion_file_headings = {
  "JLCPCB":		["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer","Originalref"],
  "Hitech PCB":	["Designator", "Comment", "Layer", "Footprint", "Center-X", "Center-Y", "Rotation","Description"],
  "PCBgogo":	["Designator", "Comment", "Layer", "Footprint", "Center-X(mil)", "Center-Y(mil)", "Rotation","Description"],
  "AllPCB":	["Designator", "Center-X(mm)", "Center-Y(mm)", "Rotation", "Layer"],
}
position_columns_selection = {
 "JLCPCB":		[1,2,3,4,5,6,7,8],
 "Hitech PCB":	[1,2,7,3,4,5,6,10],
 "PCBgogo":	    [1,2,7,3,4,5,6,10],
 "AllPCB":	    [1,4,5,6,7],
}
BOM_file_headings = {
  "JLCPCB": ["Comment", "Designator", "Footprint", "LCSC Part Number", "MPN", "MFG"],
  "Hitech PCB": ["ID", "Designator", "Name", "Quantity", "Manufacturer Part Number", "Manufacturer"],
  "PCBgogo": ["Quantity", "Designator", "Description", "Value", "Footprint", "Manufacturer", "Part Number"],
  "AllPCB": ["Quantity", "Designator", "Description", "Value", "Footprint", "Manufacturer", "Part Number"],
}
BOM_columns_selection = {
  "JLCPCB": [1,2,3,4,7,6],
  "Hitech PCB": [0,2,1,5,4,6],
  "PCBgogo": [5,2,1,1,3,6,4],
  "AllPCB": [5,2,1,1,3,6,4],
}
layer_names = {
  "JLCPCB": {'"F.Cu"':"top", '"B.Cu"':"bottom"},
  "Hitech PCB": {'"F.Cu"':"TopLayer", '"B.Cu"':"BottomLayer"},
  "PCBgogo": {'"F.Cu"':"TopLayer", '"B.Cu"':"BottomLayer"},
  "AllPCB": {'"F.Cu"':"TopLayer", '"B.Cu"':"BottomLayer"},
}

import sqlite3
conn = sqlite3.connect("cache.sqlite3")
cursor = conn.cursor()
#cursor.execute('CREATE INDEX idx_mfr ON components (mfr)')

import re

def footprint_equivalence(footprint):
  pattern = r'".*:[RCLD]_(\d+)_.*?Metric"'
  parts = footprint.split(':')

  match = re.match(pattern, footprint)
  if match:
    return match.group(1), parts[-1]

  pattern = r'".*:[RCLD](\d+)\-NSK"'
  match = re.match(pattern, footprint)
  if match:
    return match.group(1), parts[-1][:-1]

  if len(parts) >= 2:
    return '"'+parts[1], parts[-1][:-1]
  return footprint, footprint[-1][:-1]

def is_common_footprint(f):
  return len(f) == 4 and f.isdigit()

prefixes = {}
positions = {}
position_fixes = {
  "C2988369":	(0, -1.25, 0),		#GT-USB-7010ASV: USB 2.0 receptacle
  "C404280":	(0, 0, +180),		#MHPA1010RGBDT: Common anode RGB LED
  #"C5365285":	(0, 0, -90),		#CPU D1s-eLQFP128
  "C5197687":	(0, 0, -90),			#CPU T113-S3-eLQFP128
  "C512395":	(+0.6, 0, +90),		#PANASONIC EVQP2P02W switch
  "C571260":	(0, 0, -90),		#W25Q32JVZPIQ WSON-8 6x5mm flash
  #"C570857":	(0, 0, -90),		#EA3036CQBR PMIC QFN-20
  "C7429915":	(0, 0, 180),		#LED-0603_BLUE
  "C7371898":	(0, 0, 180),		#LED-0603_PURPLE
  "C345958":	(0, 0, 180),		#Diode MSK4010
  "C961679":	(0, -0, 180),	#TF-SMD_TF-018 SD socket
  #"C481232":	(0, -0.7, 0),		#FPC Cable connector 1x20 XFCN
  #"C481233":	(0, -0.7, 0),		#FPC Cable connector 1x30 XFCN
  "C481234":	(0, 0.5, 0),			#FPC Cable connector 1x40 XFCN
  "C2922285":	(7.0, -1.5, 180),	#TE Connectivity 1-1734248-5 FPC Cable connector 1x15
  "C427307":	(0, -2.0, 0),		#HDMI_A_Amphenol_10029449-x01xLF_Horizontal
  "C9386": (0, 0, 90), #74HC4051 SOIC-16W
  "C2905421": (-19, 0, 90), #Female 1x16 .1" pitch
  "C2905419": (-14, 0, 90), #Female 1x12 .1" pitch
  "C7499349": (-18, 0, 90), #Female 2x14 .1" pitch
  "C492401": (-1, 0, 90), #2P header .1" pitch
  "C431533": (-3, 2.3, 0), #DC jack
  "C2906032": (0, 0, 90), #2P female 2mm pitch
  "C165948": (0, -1.25, 0), #TYPE-C-31-M-12 USB female connector
  #"C15999": (0, 0, 180), #USBLC6-2P6 ESD surge protector
  "C398366": (0, 0, 180), #TLV62569APDRLR SOT-563 DC-DC
  "C190862": (0, 0, 180), #W25Q128JVPIQ 128mbit flash WSON-8
}

def rotate2d(x, y, angle):
  angle = int(angle+360) % 360
  if angle == 90:
    return y, -x
  if angle == 180:
    return -x, -y
  if angle == 270:
    return -y, x
  assert(angle == 0)
  return x, y

def rename_reference(ref):
    global prefixes, positions
    match = re.search(r'(\D+)(\d+)$', ref)
    prefix, num = (match.group(1), int(match.group(2))) if match else (ref, 1)
    if prefix not in prefixes:
      prefixes[prefix] = 0
    last_used_num = prefixes[prefix]
    current_num = num if ref not in positions else last_used_num + 1
    prefixes[prefix] = max(current_num, last_used_num)
    return prefix + str(current_num)

def resistor_value_map(value):
  value=value.upper()
  if len(value)>=4 and value[-1] in "RMK" and value[-3]==".":
    value = bytearray(value, 'ascii')
    value[-3]=value[-1]
    return value.decode("ascii")[:-1]
  if value[-1] in "RMK":
    return value
  if value.isdigit():
      return value+"R"
  if len(value)>=3 and value[-2]=="K":
    return value #example 5K1
  return None
  
#examples
# RC0201DR-07120KL for 120K 0201
# RC0402JR-075K1L for 5.1k 0402
# RC0603JR-0747KL for 47K 0603
# RC0201FR-07210KL for 210K 1% 0201
# CRCW0805210KFKED for 210K 1% 0805
# CRCW0402210KFKED for 210K 1% 0402
# CL21B106KOQNNNE for 10uF 0805
# CL10A106MP8NNNC / CL10A106MQ8NNNC for 10uF 0603
# CL05A104KA5NNNC for 100nF 0402
# CC0402JRNPO9BN150 for 15p 0402
# CL31B104KBCNNNC for 100nF 1206

def is_common_part(qualified_footprint):
  if len(qualified_footprint) < 2:
    return False
  return qualified_footprint[:2] in ["R_","L_","C_"]
    
def find_similar_parts(mpn):
  if len(mpn) > 9:
    mpn = mpn[:-3]
  sql = "SELECT mfr FROM components where mfr between ? and ? LIMIT 3"
  cursor.execute(sql, (mpn, mpn+"{",))
  row = cursor.fetchall()
  return [x[0] for x in row]

common_part_db = {}
def find_common_part(qualified_footprint, footprint, fullvalue): #resistors, capacitors, etc
  global common_part_db
  values = fullvalue.upper().split()
  assert(len(values))
  value = values[0]
  tolerance = "" if len(values)<2 else values[1]
  
  key = (qualified_footprint, value)
  if key in common_part_db:
    return common_part_db[key], True

  mfr, part = None, None
  if qualified_footprint[0] == "R":
    value = resistor_value_map(value)
    if value is not None:
      if tolerance == "1%":
        mfr, part = "YAGEO", f"RC{footprint}FR-07{value}L"
        if False and value[-1] == "K":
          if len(value) == 3:
            value += "0"
            mfr, part = "VISHAY", f"CRCW{footprint}{value}FKED"
      if tolerance == "0.5%":
        mfr, part = "YAGEO", f"RC{footprint}DR-07{value}L"
      if tolerance == "":
        #mfr, part = "YAGEO", f"AF{footprint}JR-07{value}L"
        #mfr, part = "YAGEO", f"RC{footprint}FR-07{value}L" #FR for 1%
        #0805W8F3001T5E UNI-ROYAL 3K3
        #0805W8F330JT5E UNI-ROYAL 33
        #0805W8F6800T5E UNI-ROYAL 680
        mfr = "UNI-ROYAL"
        if value == "0R":
          value = "0000"
        elif value[-2] in "K" and len(value) == 3:
          value = value[:-2] + value[-1] + "01"
        elif value[-1] in "R" and len(value) == 3:
          value = value[:-1] + "0J"
        elif value[-1] in "R" and len(value) == 4:
          value = value[:-1] + "0"
        elif value[-1] in "K" and len(value) == 3:
          value = value[:-1] + "02"
        elif value[-1] in "M" and len(value) == 2:
          value = value[:-1] + "004"
        else:
          mfr, part = "YAGEO", f"RC{footprint}JR-07{value}L" #YAGEO manufacturer format (or DR FOR 0.5%)
        if mfr == "UNI-ROYAL":
	        if footprint == "0402":
	          part = f"0402WGF{value}TCE"
	        elif footprint == "0201":
	          part = f"0201WMF{value}TEE"
	        else:
	          part = f"{footprint}W8F{value}T5E"
	        

  #print("\n\nfind_common_part", qualified_footprint, footprint, value)
  elif qualified_footprint[0] == "C":
    if value[-1] in "PNU":
      value += "F"
    if value[-1]=='F' and value[-2] in "PNU":
      expten = {"P":0,"N":3,"U":6}[value[-2]]
      value = value[:-2]
      if float(value) < 1:
        value = str(int(float(value) * 1000))
        expten -= 3
      if float(value) < 10 and len(value)>2 and value[1]==".":
        value = str(int(float(value) * 1000))
        expten -= 3
        #print("\n\nfullvalue", fullvalue, "value", value, "zeros", value[2:], "base", value[:2], "expten", expten, "footprint", footprint, "qualified_footprint", qualified_footprint)
        #quit()

      base = value[:2]
      if len(base) == 1:
        base += "0"
        expten -= 1
      zeroes = value[2:]
      expten += len(zeroes)
  
      picofarads = base + str(expten)

      allzeros = all(char == '0' for char in zeroes)
      if not allzeros:
        print("ERROR: wrong component value", value, "zeroes", zeroes, "fullvalue", fullvalue, "footprint", qualified_footprint)

      assert(allzeros)
      mfr = "Samsung Electro-Mechanics"
      if footprint == "1206":
        part = f"CL31B{picofarads}KBCNNNC"
      elif footprint == "0805":
        part = f"CL21B{picofarads}KOQNNNE"
      elif footprint == "0603":
        #part = f"CL10A{picofarads}KA8NNNC" #25v
        #part = f"CL10A{picofarads}MP8NNNC" #10v 20%
        #part = f"CL10A{picofarads}MA8NRNC" #25v 20%
        #part = f"CL10A{picofarads}MQ8NNNC" #6.3v 20%
        if expten >= 6:
          #part = f"CL10A{picofarads}KO8NQNC" #16v 10%
          part = f"CL10A{picofarads}MQ8NNNC" #6.3v 20%
        elif expten > 4:
          part = f"CL10A{picofarads}KO8NNNC" #16v 10%
        else:
          part = f"CL10B{picofarads}KB8NNNC" #50V 10%
        #print(f"**** try {footprint} capacitor {picofarads}, expten {expten}:", part)
      elif footprint == "0402":
        if expten > 4:
          part = f"CL05A{picofarads}KA5NQNC" #25v 10%
        elif expten > 0:
          part = f"CL05A{picofarads}KA5NNNC" #25v 10%
        else:
          mfr = "YAGEO"
          part = f"CC0402JRNPO9BN{picofarads}" #50v 5%

  common_part_db[key] = (part, mfr)
  return (part, mfr), False


def db_part_lookup(mpn):
  global cursor, mpn_database
  
  if mpn in mpn_database:
    return mpn_database[mpn]
  
  sql = 'SELECT lcsc,name, description FROM components INNER JOIN manufacturers ON components.manufacturer_id=manufacturers.id where mfr=? LIMIT 2'
  cursor.execute(sql, (mpn,))
  row = cursor.fetchone()
  part_number, mfr, part_desc = ("C"+str(row[0]), row[1], row[2]) if row is not None else (None, None, None)

  if part_desc is None:
    part_desc = ""
  if len(part_desc) > 15:
    part_desc = " ".join(part_desc.split()[:3])

  mpn_database[mpn] = (part_number, mfr, part_desc)
  return part_number, mfr, part_desc
          

mpn_database = {}
part_manufacturers = {}
renamed_refs = []
empty_parts = []
errors_count = 0
warnings_count = 0
part_tags = [x.upper() for x in part_tags] #uppercase all part tags
total_pad_count = 0
placed_pad_count = 0
for a in pcb.footprint:
  skip_placement = 'attr' in a._value and ('exclude_from_pos_files' in a.attr or 'dnp' in a.attr or "exclude_from_bom" in a.attr)
  if skip_placement:
    continue
  if "tags" in a._value and "fiducial" in a.tags:
    continue
  
  reference_tag = '"Reference"'
  value_tag = '"Value"'
  ref_property = a.property[0] #FIXME: don't assume position for "Reference" property
  value_property = a.property[1]  #FIXME: don't assume position for "Value" property
  assert(ref_property[0] == reference_tag)
  assert(value_property[0] == value_tag)
  value = value_property[1]
  assert(value[0] == '"' and value[-1] == '"')

  oldref = ref_property[1]
  assert(oldref[0] == '"' and oldref[-1] == '"')
  oldref = oldref[1:-1].strip()
  footprint = a[0].strip()
  assert(footprint[0] == '"' and footprint[-1] == '"')

  reference = rename_reference(oldref)
  if reference != oldref:
    renamed_refs += [(oldref, reference)]
    #print("rename", oldref, "to", reference);

  assert(a.layer in ['"F.Cu"', '"B.Cu"'])
  layer = layer_names[fab_format][a.layer]
  footprint, qualified_footprint = footprint_equivalence(footprint)

  at = a.at
  if len(at) < 3:
    assert(len(at) == 2)
    at += [0] #it seems normal not to include rotation info for 0 degrees, add it
  x, y, rot = at

  dnp = False
  mpn = None
  mfr = None
  chosen_part = None
  footprint_attr = None

  part_desc = "unknown description" #FIXME: assign to anything existing
  if "descr" in a._value:
    part_desc = a.descr
    assert(part_desc[0] == '"' and part_desc[-1] == '"')
    part_desc = part_desc[1:-1]
  
  
  for b in a.property:
    property_attr = str(b[0])
    if property_attr.lower() == '"dnp"':
      dnp = True
      break
    prop_value = b[1]
    assert(prop_value[0] == '"' and prop_value[-1] == '"')
    prop_value = prop_value[1:-1].strip()
    part_number = prop_value.upper()
    prop = property_attr.upper()[1:-1]
    if prop == "DESCRIPTION":
      assert(b[1][0] == '"' and b[1][-1] == '"')
      if prop_value!="":
        part_desc = prop_value
    elif prop == "FOOTPRINT":
      footprint_attr = part_number
    elif prop == manufacturer_tag.upper():
      mfr = prop_value
    elif prop in part_tags and not (is_common_part(qualified_footprint) and prop == "VALUE"):
      if chosen_part is None and part_number != "":
        mpn = part_number
        if fab_tag != "":
          part_number, mfr, part_desc = db_part_lookup(mpn)
        #if part_number is not None:
        #  break #comment to give priority to fab_tag
        if part_number is not None:
          chosen_part = part_number #may be overriden by FAB tag
    elif prop not in ["REFERENCE"]:
      #print("\n\nTRYING", part_number, reference, "prop", prop, "fab_tag", fab_tag)
      if fab_tag != "" and prop == fab_tag.upper():
        if part_number != "":
          #check footprint
          if is_common_footprint(footprint):
            sql = 'SELECT package FROM components where lcsc=? LIMIT 1';
            cursor.execute(sql, (part_number[1:],))
            row = cursor.fetchone()
            if row is None:
              print("\033[93mWARNING\033[0m: No footprint found for reference", reference+", set as", footprint, "part number", part_number)
            elif row[0] != footprint:
              print("\033[91mERROR\033[0m: footprint mismatch for reference", reference+ ", it is set as", footprint, "but real footprint is", row[0], "part number", part_number)
              part_number = None
              errors_count += 1
        
          chosen_part = part_number
          break # FAB number set, or bad footprint
        else:
          empty_parts += [reference]
        

  part_number = chosen_part
  if part_number == "":
    part_number = None
  if footprint in ['"NPTH"']:
    part_number = None
    value = '""'

  if part_number is None and value != '""':
    #print("qualified_footprint, footprint", qualified_footprint, ",", footprint)
    (alt_mpn, mfr), common_hit = find_common_part(qualified_footprint, footprint, value[1:-1])
    if alt_mpn is not None:
      #print("\n\nALT MPN", alt_mpn, "MFR", mfr)
      if fab_tag != "":
        part_number, mfr, part_desc = db_part_lookup(alt_mpn)
        mpn = alt_mpn
        #if part_number is None:
        #  print("\n\nCannot find in DB:", alt_mpn)
      else:
        part_number = alt_mpn
      if part_number is not None:
        if not common_hit:
          maps_to = " (maps to "+part_number+")" if alt_mpn != part_number else ""
          print("\033[93mWARNING\033[0m: Using aternative part", alt_mpn  + maps_to, "for", value, "in package", footprint)
          warnings_count += 1
  
  if part_number is not None:
    if part_number in position_fixes: #TODO: also consider cpl_rotations_db.csv
      rot_correction = position_fixes[part_number]
      print("\033[93mWARNING\033[0m: Corrected placement for reference", oldref, "(part", part_number+")", footprint)
      warnings_count += 1
      print("\033[92mINFO\033[0m:", oldref, part_desc, "should have JLCPCB_CORRECTION set to:", "; ".join([str(k) for k in rot_correction]))
      rot = (rot + rot_correction[2] + 180.0) % 360 - 180
      dx, dy = rotate2d(rot_correction[0], rot_correction[1], rot) #fix rotation
      x += dx
      y += dy

    if mfr is None and fab_tag=="":
      if part_number in part_manufacturers:
        mfr = part_manufacturers[part_number]
      else:
        _, mfr, _ = db_part_lookup(part_number)
        part_manufacturers[part_number] = mfr
        if mfr is None:
          print("\033[91mERROR\033[0m:", reference, "with part", part_number, "has unknown manufacturer")
          errors_count += 1
        else:
          print("\033[93mWARNING\033[0m: Manufacturer for part", '"'+part_number+'"', "seems to be", '"'+mfr+'"', "(consider setting", '"'+manufacturer_tag+'"', "with that)")
          warnings_count += 1

    assert(reference not in positions)
    positions[reference] = [value, footprint, str(x), str(-y), str(rot), layer, '""' if oldref == reference else oldref, part_number, '"'+part_desc+'"', '"'+mfr+'"' if mfr is not None else '""', '"'+mpn+'"' if mpn is not None else '""']
    placed_pad_count += len(a.pad)
    #print("\033[94mDEBUG\033[0m: Adding", reference, part_number, value, footprint)

  elif not dnp:
    #print("\n\nValue", value, "footprint_attr", footprint_attr, "full footprint", qualified_footprint)
    if footprint_attr == "" and value == '"' + qualified_footprint + '"':
      coord = ",".join(str(x) for x in a.at[:2])
      print("\033[93mWARNING\033[0m: excluding reference", oldref, "at", coord+":", 'no Footprint attribute set (or equal to Value)', )
      warnings_count += 1
    else:
      tags = " or ".join(['"'+tag+'"' for tag in (part_tags+[fab_tag] if fab_tag != "" else part_tags)])
      print("\033[91mERROR\033[0m: Missing", tags, "attribute(s) for", '"'+oldref+'"', "value", value, "at", a.at[:2], "" if mpn is None else "(MPN:"+mpn+")", "footprint", qualified_footprint)
      if mpn is not None:
        similar_mpns = find_similar_parts(mpn)
        if len(similar_mpns):
          print("\033[92mINFO\033[0m: consider similar parts", ", ".join(similar_mpns))
        else:
          mpn = None
         
      if mpn is None:
        print("\033[92mINFO\033[0m: if", '"'+oldref+'"', "is not a component, consider not populating or excluding it from position file")
      
      errors_count += 1

  total_pad_count += len(a.pad)

if len(empty_parts):
  print("\033[93mWARNING\033[0m: Ignoring empty", fab_tag, "attribute for parts", ", ".join(empty_parts))
  warnings_count += 1

if len(renamed_refs):
  print("\033[93mWARNING\033[0m: Renamed duplicated references:", ", ".join([a + " to " + b for a,b in renamed_refs]))
  print('\033[92mINFO\033[0m: You can safely ignore the above warning, or for 1:1 relationship with the PCB file with unique references, consider using Kicad\'s "Geographical reannotate" tool')
  warnings_count += 1

BOM = {}

base_name = os.path.splitext( os.path.abspath(fname))[0]
pos_name = base_name + "_pos.csv"
bom_name = base_name + "_bom.csv"

with open(pos_name, 'w') as f:
   col_sel = position_columns_selection[fab_format]
   print(",".join(postion_file_headings[fab_format]), file=f)
   ID = 1
   for reference, pos in positions.items():
     columns = [str(ID)] + [reference] + pos
     print(",".join([columns[i] for i in col_sel]), file=f)
     part_number = pos[7]
     #print("part_number", part_number)
     ref_list = BOM[part_number][0] + [reference] if part_number in BOM else [reference]
     BOM[part_number] = (ref_list, pos[0], pos[1], pos[9], pos[10]) #Reference, part, footprint, mfr, mpn
     ID += 1

with open(bom_name, 'w') as f:
   col_sel = BOM_columns_selection[fab_format]
   print(",".join(BOM_file_headings[fab_format]), file=f)
   ID = 1
   for part_number, d in BOM.items():
     ref_list, value, footprint, mfr, mpn = d
     qty = str(len(ref_list))
     ref_list = '"' + ",".join(ref_list) + '"'
     columns = [str(ID), value, ref_list, footprint, part_number, qty, mfr, mpn]
     print(",".join([columns[i] for i in col_sel]), file=f)
     ID += 1

if "AllPCB" in fab_format:
  import pandas
  f = pandas.read_csv('POS.csv')
  f.to_excel('POS.xlsx', index=False)
  f = pandas.read_csv('BOM.csv')
  f.to_excel('BOM.xlsx', index=False)

found_parts=[part_number[0] + '\tfor ' + mpn + ": " + part_number[2] + "\t[" + part_number[1] + "]" for mpn, part_number in mpn_database.items() if part_number[0] is not None]
if len(found_parts):
  print("\033[92mINFO\033[0m: Found", len(found_parts), "parts by Manufacturer part number in FAB database:")

for part in found_parts:
  print("\033[92mINFO\033[0m:", part)

#missing_parts=[mpn for mpn, part_number in mpn_database.items() if part_number is None]
#print("\033[91mERROR\033[0m: Parts not found in FAB database:", ", ".join(missing_parts))
for mpn, part_number in mpn_database.items():
  if part_number is None:
    print("\033[93mWARNING\033[0m: Manufacturer part", '"'+mpn+'"', "not found in FAB database")
    warnings_count += 1



print("\033[92mINFO\033[0m: Pad count", total_pad_count, "("+str(placed_pad_count)+" placed)")
print("BOM and POS output fles: ", bom_name, pos_name)
print("\nResults:", errors_count, "errors,", warnings_count, "warnings")
exit(errors_count > 0)




