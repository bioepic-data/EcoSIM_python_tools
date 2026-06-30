import os
import requests
import zipfile
import time

# --- SETTINGS ---
start_year = 2024
end_year = 2024  # Adjust based on availability
output_root = "./nadp_data_grids"

# List of species based on your URLs
ions = [
    "pH", "SO4", "NO3", "NH4", "Ca",
    "Mg", "K", "Na", "Cl"
]

# Base URL pattern
# Example: https://nadp.slh.wisc.edu/filelib/maps/NTN/grids/1988/pH_conc_1988.zip
url_template = "https://nadp.slh.wisc.edu/filelib/maps/NTN/grids/{year}/{ion}_conc_{year}.zip"

# Create root directory
os.makedirs(output_root, exist_ok=True)

for year in range(start_year, end_year + 1):
    print(f"\n--- Processing Year: {year} ---")

    # Create a subfolder for the year
    year_dir = os.path.join(output_root, str(year))
    os.makedirs(year_dir, exist_ok=True)

    for ion in ions:
        url = url_template.format(year=year, ion=ion)
        file_name = f"{ion}_conc_{year}.zip"
        zip_path = os.path.join(year_dir, file_name)

        try:
            # Using a custom User-Agent can help prevent blocks from some servers
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, stream=True, timeout=15)

            if response.status_code == 200:
                # Save the zip
                with open(zip_path, 'wb') as f:
                    f.write(response.content)

                # Extract the zip
                # This usually creates a folder or a set of .asc/.tif files
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Extract into the year folder
                        zip_ref.extractall(year_dir)
                    print(f"  [OK] {ion}")
                    # Remove zip after extraction to save space
                    os.remove(zip_path)
                except zipfile.BadZipFile:
                    print(f"  [ERROR] {ion}: Downloaded file is not a valid zip.")

            elif response.status_code == 404:
                # Silently skip or print missing
                pass
            else:
                print(f"  [SKIP] {ion}: Status {response.status_code}")

        except Exception as e:
            print(f"  [FAILED] {ion}: {e}")

    # Short pause to be polite to the server
    time.sleep(0.5)

print("\nAll downloads and extractions complete.")