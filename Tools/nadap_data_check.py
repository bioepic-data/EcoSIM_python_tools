import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

# Path to your file
file_path = 'nadp_data_grids/1985/K_conc_1985/conc_k_1985.tif'

with rasterio.open(file_path) as src:
    # Read the first band
    data = src.read(1)

    # Use the internal nodata value if set, otherwise use -900 as a threshold
    nodata = src.nodata if src.nodata is not None else -900

    # Create a masked array to hide NoData areas (values outside CONUS)
    masked_data = np.ma.masked_where(data <= nodata, data)

    # Setup the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot using imshow for better control over the colorbar
    # Using 'viridis' or 'YlGnBu' colormaps works well for concentrations
    img = ax.imshow(masked_data, extent=rasterio.plot.plotting_extent(src), cmap='viridis')

    # Add a colorbar
    cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('Concentration ($mg/L$)')

    # Add titles and labels
    ax.set_title('Potassium ($K^+$) Concentration - 1985', fontsize=14)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Save or show
    plt.savefig('potassium_1985_map.png', dpi=300, bbox_inches='tight')
    plt.show()