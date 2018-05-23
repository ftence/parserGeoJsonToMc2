# Script to parse GEOJSON files into MC2 macros.
# @author aurrelhebert
# @license apache 2.0
#

import json
import os
import unidecode
import sys
import re


def get_value_from_expression(json_node, expression):
    # Allow path to be used
    path = expression.split('/')
    current_node = json_node

    # Walk along the path to find the name
    for path_item in path:
        current_node = current_node.get(path_item)
        if current_node is None:
            raise ValueError('Could not find {} in JSON {}.'.format(expression, json_node))

    if not isinstance(current_node, str):
        raise TypeError('{} does not match a str value in the JSON {}.'.format(expression, json_node))

    return current_node


def clean_str(the_string, old_method=False):
    if old_method:
        return re.sub('[^A-Za-z0-9]+', ' ', the_string).lower()
    else:
        return re.sub('[^A-Za-z0-9]+', ' ', unidecode.unidecode(the_string)).lower()


def main(args):
    # Load JSON conf
    conf_file = 'geojson.conf'
    input_conf = open(conf_file, 'r')
    json_conf = json.load(input_conf)

    # Each element of the conf corresponds to one GeoJson file
    for geoJsonConf in json_conf:

        # Load GEO.JSON file linked in conf
        source_file_name = geoJsonConf.get('filename')
        input_file = open(source_file_name, 'r')
        json_decode = json.load(input_file)

        # Load current GEOSJON precision
        error_percentage = geoJsonConf.get('errorPercentage', '0.1')
        inside = geoJsonConf.get('inside', 'true')

        # Get GEOJSON file features (includes the geometry and properties)
        features = json_decode.get('features')

        # Allow legacy str cleaning to avoid wrecking havok in production using old str cleaning
        legacy_str_cleaning = geoJsonConf.get('legacy_str_cleaning', False)
        # Also for legacy reasons, keep a list of generated file names to avoid generating twice if new and old str
        # cleaning yield the same result
        filenames = set()

        # Apply title or not on the filename (True by default)
        titlize_name = geoJsonConf.get('titlize', True)

        split_list_macro = geoJsonConf.get('splitPerDirectory', False)
        complete_list = '<% [ '

        item_for_list = {}

        if legacy_str_cleaning:
            use_legacy_str_cleaning = [True, False]  # Generate both dirty and clean names
        else:
            use_legacy_str_cleaning = [False]  # Only generate clean names

        for legacy_str_cleaning_flag in use_legacy_str_cleaning:
            for item in features:

                # Load prefix directory set in conf
                # This used to set for example the country
                directory = geoJsonConf.get('prefix')

                # Appends directory with each name of the properties define in directories in conf
                # This is used to generate subname for the current directory as region or state
                properties_node = item.get('properties')
                for repository in geoJsonConf.get('directories'):
                    name = get_value_from_expression(properties_node, repository)
                    directory = directory + clean_str(name, legacy_str_cleaning_flag).replace(" ", "_") + "/"

                # Load warpscript file name from the conf (if exists otherwise don't change it's value)
                warp_script_file_name = geoJsonConf.get('warpscriptName', '')

                # If warpscript file name is not define
                if '' == warp_script_file_name:

                    # Load from the conf WarpScript load
                    json_load = geoJsonConf.get('warpscriptLoad', '')

                    # when conf exists allowing the user to choose the file name from GEOJSON attribute
                    if not '' == json_load:
                        # Then get from the GEOJSON properties the current WarpScript file name
                        current_file_name = get_value_from_expression(item.get('properties'), json_load)
                        clean_current_file_name = clean_str(current_file_name, legacy_str_cleaning_flag)
                        if titlize_name:
                            clean_current_file_name = clean_current_file_name.title()
                        warp_script_file_name = clean_current_file_name.replace(" ", "_")

                # When an output file name is set in conf
                if not '' == warp_script_file_name:

                    # Create local directory
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    filename = directory + warp_script_file_name + '.mc2'

                    if filename in filenames:
                        continue
                    else:
                        filenames.add(filename)

                    # Write WarpScript macro in file based on current data and conf
                    f = open(filename, 'w')
                    f.write("'" + json.dumps(item.get('geometry')) + "' \n")
                    f.write(error_percentage + " " + inside + " GEO.JSON \n")
                    f.write("'_geo' STORE \n")
                    f.write("<% \n")
                    f.write(" !$_geo \n")
                    f.write("%> \n")
                    f.close()

                # Write list indicating all macro stored
                if not split_list_macro:
                    complete_list = complete_list + " '@orbit/" + directory + warp_script_file_name + "'"

                # In case you generate one file per directory
                if split_list_macro:

                    # Add file to current directory key
                    if directory in item_for_list:
                        current_list = item_for_list.get(directory) + " '@orbit/" + directory + warp_script_file_name + "'"
                        item_for_list[directory] = current_list
                    else:
                        current_list = complete_list + " '@orbit/" + directory + warp_script_file_name + "'"
                        item_for_list[directory] = current_list

        # Finish WarpScript list and macro
        complete_list = complete_list + " ] %>"

        # Store complete list in a macro only if user specify a file nime to use in conf file
        all_macro = geoJsonConf.get('allMacroFileName', '')

        if not '' == all_macro:

            # Write file containing all macro in root directory according to conf parameters set
            if not split_list_macro:
                # Write complete macro list inside a WarpScript macro file
                f = open(geoJsonConf.get('prefix') + all_macro + '.mc2', 'w')
                f.write(complete_list)
                f.close()

            # Case split according to files
            if split_list_macro:
                for key in item_for_list.keys():
                    current_list = item_for_list.get(key)
                    current_list = current_list + " ] %>"

                    # Write complete macro list inside a WarpScript macro file
                    f = open(key + all_macro + '.mc2', 'w')
                    f.write(current_list)
                    f.close()


if __name__ == "__main__":
    main(sys.argv)
