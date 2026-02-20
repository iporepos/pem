.. dropdown:: PEM Project file system layout
    :icon: file-directory-fill
    :open:

    .. code-block:: text

        pem-project/                           # Project base folder
        │
        ├── inputs/                            # Folder for all model inputs
        │   │
        │   ├── bathymetry.tif                 # Canonical raster (resolution, extent, CRS)
        │   │
        │   ├── vectors.gpkg                   # Core vector data container
        │   ├── vectors.gpkg|roi               # Region of Interest (polygon layer)
        │   ├── vectors.gpkg|hubs              # Land hubs (point layer)
        │   ├── vectors.gpkg|habitat_benthic   # Benthic habitat map with attributes
        │   ├── vectors.gpkg|habitat_pelagic   # Pelagic habitat map with attributes
        │   ├── vectors.gpkg|...               # Additional optional layers
        │   │
        │   ├── _sources/                      # Helper folder for sourced datasets
        │   │
        │   ├── benefit/                       # Benefit Index parameters and data
        │   │
        │   ├── habitats/                      # Habitat rasters
        │   │   ├── benthic.tif                # Rasterized Benthic habitat map
        │   │   └── pelagic.tif                # Rasterized Pelagic habitat map
        │   │
        │   ├── risk/                          # Habitat Risk model parameters
        │   │   ├── baseline/
        │   │   │   ├── stressors_benthic.csv  # Stressor table (required by InVEST-HRA)
        │   │   │   ├── scores_benthic.csv     # Criteria scores (required by InVEST-HRA)
        │   │   │   ├── stressors_pelagic.csv
        │   │   │   └── scores_pelagic.csv
        │   │   │
        │   │   └── {scenario}/                # Alternative scenarios
        │   │
        │   ├── roi/
        │   │   ├── roi.shp                    # Shapefile for ROI (required by InVEST-HRA)
        │   │   └── roi.tif                    # Boolean raster for ROI
        │   │
        │   └── users/                         # Ocean users configuration
        │       ├── users.csv                  # Table of ocean users
        │       ├── users_conflict.csv         # Spatial conflict matrix
        │       │
        │       ├── baseline/                  # Baseline scenario
        │       │   ├── oilngas.tif            # raster footprint or density
        │       │   ├── fisheries.tif          # (suggested users)
        │       │   ├── windfarms.tif
        │       │   ├── {username}.tif
        │       │   └── ...
        │       │
        │       └── {scenario}/                # Alternative scenarios
        │
        └── outputs/                           # Model outputs
            │
            ├── baseline/
            │   ├── baseline_iduse.tif         # Use Performance Index
            │   ├── baseline_benefit.tif       # Benefit Index
            │   ├── baseline_conflict.tif      # Conflict Index
            │   ├── baseline_risk.tif          # Habitat Risk Index
            │   │
            │   └── intermediate/              # Intermediate artifacts
            │       ├── baseline_hra_benthic.tif      # InVEST output
            │       ├── baseline_hra_benthic_fz.tif   # fuzzy transform
            │       ├── baseline_hra_pelagic.tif
            │       └── baseline_hra_pelagic_fz.tif
            │
            └── {scenario}/                    # Alternative scenario outputs
