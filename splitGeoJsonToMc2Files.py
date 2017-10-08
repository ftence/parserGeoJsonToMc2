# Script to split GEOJSON files into MC2 macro
# @author aurrelhebert
# @license apache 2.0
#

import json
import os
import re
import codecs

# Load JSON conf
confFile='geojson.conf'
inputConf=open(confFile, 'r')
jsonConf=json.load(inputConf)

# Load GEO.JSON file linked in conf
sourceFileName=jsonConf.get('filename')
inputFile=open(sourceFileName, 'r')
jsonDecode=json.load(inputFile)

# Get GEOJSON file features (includes the geometry and properties)
features=jsonDecode.get('features')
completeList="<% [ "

for item in features:

  # Load prefix directory set in conf
  # This used to set for example the country
  directory=jsonConf.get('prefix')

  # Appens directory with each name of the properties define in directories in conf
  # This is used to generate subname for the current directory as region or state
  for repository in jsonConf.get('directories'):
    name = item.get('properties').get(repository).replace(" ", "_")
    nameClean = re.sub('[^A-Za-z0-9]+', ' ', name).lower()
    directory= directory + nameClean.replace(" ", "_") + "/"

  # Initial WarpScript file name
  warpScriptFileName=""

  # Load warpscript file name from the conf (if exists otherwise don't change it's value)
  warpScriptFileName=jsonConf.get('warpscriptName', "")

  # If warpscript file name is not define
  if "" == warpScriptFileName:

    # Load from the conf WarpScript load
    jsonLoad=jsonConf.get('warpscriptLoad', "")

    # when conf exists allowing the user to choose the file name from GEOJSON attribute
    if not "" == jsonLoad:
      # Then get from the GEOJSON properties the current WarpScript file name
      currentFileName=item.get('properties').get(jsonLoad).replace(" ", "_")
      warpScriptFileName=re.sub('[^A-Za-z0-9]+', ' ', currentFileName).lower().title().replace(" ", "_")

  # When an output file name is set in conf
  if not "" == warpScriptFileName:

    # Create local directory
    if not os.path.exists(directory):
      os.makedirs(directory)

    # Write WarpScript macro in file based on current data and conf
    f = open(directory + warpScriptFileName + '.mc2', 'w')
    f.write("'" + json.dumps(item.get('geometry')) + "' \n")
    f.write("0.001 false GEO.JSON \n")
    f.write("'_geo' STORE \n")
    f.write("<% \n")
    f.write(" !$_geo \n")
    f.write("%> \n")
    f.close()

  # Write list indicating all macro stored
  completeList= completeList + " '@orbit/geo/" + directory + warpScriptFileName + "'"

# Finish WarpSctip list and macro
completeList=completeList + " ] %>"

# Write complete macro list inside a WarpScript macro file
f = open(jsonConf.get('prefix') + 'Items.mc2', 'w')
f.write(completeList)
f.close()


