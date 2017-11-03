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

# Each element of the conf corresponds to one GeoJson file
for geoJsonConf in jsonConf:

  # Load GEO.JSON file linked in conf
  sourceFileName=geoJsonConf.get('filename')
  inputFile=open(sourceFileName, 'r')
  jsonDecode=json.load(inputFile)

  # Load current GEOSJON precision
  errorPercentage=geoJsonConf.get('errorPercentage', '0.1')
  inside=geoJsonConf.get('inside', 'true')

  # Get GEOJSON file features (includes the geometry and properties)
  features=jsonDecode.get('features')

  splitListMacro=geoJsonConf.get('splitPerDirectory', False);
  completeList="<% [ "

  itemForList={}

  for item in features:

    # Load prefix directory set in conf
    # This used to set for example the country
    directory=geoJsonConf.get('prefix')

    # Appens directory with each name of the properties define in directories in conf
    # This is used to generate subname for the current directory as region or state
    for repository in geoJsonConf.get('directories'):
      name = item.get('properties').get(repository).replace(" ", "_")
      nameClean = re.sub('[^A-Za-z0-9]+', ' ', name).lower()
      directory= directory + nameClean.replace(" ", "_") + "/"

    # Initial WarpScript file name
    warpScriptFileName=""

    # Load warpscript file name from the conf (if exists otherwise don't change it's value)
    warpScriptFileName=geoJsonConf.get('warpscriptName', "")

    # If warpscript file name is not define
    if "" == warpScriptFileName:

      # Load from the conf WarpScript load
      jsonLoad=geoJsonConf.get('warpscriptLoad', "")

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
      f.write(errorPercentage + " " + inside + " GEO.JSON \n")
      f.write("'_geo' STORE \n")
      f.write("<% \n")
      f.write(" !$_geo \n")
      f.write("%> \n")
      f.close()

    # Write list indicating all macro stored
    if not splitListMacro:
      completeList = completeList + " '@orbit/" + directory + warpScriptFileName + "'"

    # In case you generate one file per directory
    if splitListMacro:

      # Add file to current directory key
      if directory in itemForList:
        currentList = itemForList.get(directory) + " '@orbit/" + directory + warpScriptFileName + "'"
        itemForList[directory] = currentList
      else:
        currentList = completeList +  " '@orbit/" + directory + warpScriptFileName + "'"
        itemForList[directory] = currentList

  # Finish WarpSctip list and macro
  completeList=completeList + " ] %>"

  # Store complete list in a macro only if user specify a file nime to use in conf file
  allMacro=geoJsonConf.get('allMacroFileName', "")

  if not "" == allMacro:

    # Write file containing all macro in root directory according to conf parameters set
    if not splitListMacro:

      # Write complete macro list inside a WarpScript macro file
      f = open(geoJsonConf.get('prefix') + allMacro + '.mc2', 'w')
      f.write(completeList)
      f.close()

    # Case split according to files
    if splitListMacro:
      for key in itemForList.keys():
        currentList = itemForList.get(key)
        currentList = currentList + " ] %>"

        # Write complete macro list inside a WarpScript macro file
        f = open(key + allMacro + '.mc2', 'w')
        f.write(currentList)
        f.close()
        print(key + allMacro + '.mc2')

