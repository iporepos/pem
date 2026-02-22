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
        │   │   ├── habitats_benthic.tif       # Rasterized Benthic habitat map
        │   │   ├── habitats_benthic.csv       # Benthic habitat table
        │   │   ├── habitats_pelagic.tif       # Rasterized Pelagic habitat map
        │   │   ├── habitats_pelagic.csv       # Benthic habitat table
        │   │   ├── benthic/                   # Benthic habitat footprints
        │   │   │   ├── {habitat-group}.tif    # habitat group footprint
        │   │   │   └── ...
        │   │   └── pelagic/                   # Pelagic habitat footprints
        │   │       ├── {habitat-group}.tif    # habitat group footprint
        │   │       └── ...
        │   │
        │   ├── risk/                          # Habitat Risk model parameters
        │   │   ├── baseline/
        │   │   │   ├── benthic_info.csv       # Benthic info table for InVEST-HRA model
        │   │   │   ├── benthic_scores.csv     # Benthic score table for InVEST-HRA model
        │   │   │   ├── benthic_model.json     # Benthic run-file for InVEST-HRA model
        │   │   │   ├── pelagic_info.csv       # Pelagic info table for InVEST-HRA model
        │   │   │   ├── pelagic_scores.csv     # Pelagic score table for InVEST-HRA model
        │   │   │   └── pelagic_model.json     # Benthic run-file for InVEST-HRA model
        │   │   └── {scenario}/                # Alternative scenarios
        │   │       └── ...
        │   │
        │   ├── roi/
        │   │   ├── roi.shp                    # Shapefile for ROI (required by InVEST-HRA)
        │   │   └── roi.tif                    # Boolean raster for ROI
        │   │
        │   └── users/                         # Ocean users configuration
        │       ├── baseline/                  # Baseline scenario
        │       │   ├── conflict.csv           # Spatial user conflict matrix
        │       │   ├── oilngas.tif            # user raster footprint or density
        │       │   ├── fisheries.tif          # (suggested users)
        │       │   ├── windfarms.tif
        │       │   ├── {username}.tif
        │       │   └── ...
        │       │
        │       └── {scenario}/                # Alternative scenarios
        │
        └── outputs/                           # Model outputs
            ├── baseline/
            │   ├── baseline_iduse.tif         # Use Performance Index
            │   ├── baseline_benefit.tif       # Benefit Index
            │   ├── baseline_conflict.tif      # Conflict Index
            │   ├── baseline_risk.tif          # Habitat Risk Index
            │   └── intermediate/              # Intermediate artifacts
            │       └── ...
            │
            └── {scenario}/                    # Alternative scenario outputs
