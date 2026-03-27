import re
import json
import sys
import argparse

def generate_single_pft_json(input_path):
    with open(input_path, 'r') as f:
        content = f.read()

    # Variables to strictly exclude 
    excluded_vars = {
        "pfts", "pfts_short", "pfts_long", 
        "koppen_clim_no", "koppen_clim_short", "koppen_clim_long"
    }

    # 1. Identify Variables and Types [cite: 3, 12, 28]
    # Matches: float VAR(npfts) ; or byte VAR(npfts) ;
    var_defs = re.findall(r'(\w+)\s+(\w+)\((?:npfts|npft|JLI|nkopenclms)(?:,\s*\w+)?\)\s*;', content)
    
    params = {}
    for var_type, var_name in var_defs:
        if var_name not in excluded_vars:
            params[var_name] = {
                "type": var_type,
                "long_name": "",
                "units": "",
                "description": "",
                "reference" : "",
                "value": None
            }

    # 2. Extract Attributes (long_name, units, flags) [cite: 3-11]
    attr_matches = re.findall(r'(\w+):(\w+)\s+=\s+"?([^";\n]+)"?', content)
    for var_name, attr_name, attr_value in attr_matches:
        if var_name in params:
            if attr_name == "long_name":
                params[var_name]["long_name"] = attr_value.strip()
            elif attr_name == "units":
                params[var_name]["units"] = attr_value.strip()
            elif attr_name == "flags":
                params[var_name]["description"] = attr_value.strip()

    # 3. Extract the first data point for each variable [cite: 116, 126, 165]
    # This looks for the start of a data assignment and grabs the first numeric value
    data_section = content.split('data:')[1] if 'data:' in content else ""
    
    for var_name in params.keys():
        # Match var_name = first_val, ... ;
        # Handles potential newlines and spaces
        pattern = rf'{var_name}\s*=\s*([^,; \n]+)'
        match = re.search(pattern, data_section)
        if match:
            raw_val = match.group(1).strip()
            try:
                # Convert to numeric if possible
                if '.' in raw_val or 'e' in raw_val.lower():
                    params[var_name]["value"] = float(raw_val)
                else:
                    params[var_name]["value"] = int(raw_val)
            except ValueError:
                params[var_name]["value"] = raw_val

    return {"pft_template": params}

                
def main():
    parser = argparse.ArgumentParser(description="Convert Ecosim CDL to a single PFT JSON template.")
    parser.add_argument("input", help="Path to the input .cdl file")
    parser.add_argument("output", help="Path to the output .json file")
    
    args = parser.parse_args()

    try:
        result = generate_single_pft_json(args.input)
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=4)
        print(f"Successfully created {args.output} from {args.input}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
# The CDL content would be passed here
# ecosim_cdl_content = """...""" 
# ecosim_json = generate_single_pft_json(ecosim_cdl_content)

# print(json.dumps(ecosim_json, indent=4))