.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module
        # ------------------------------------------------------
        module = "path/to/project.py" # change here

        # define the project folder
        # ------------------------------------------------------
        folder = "path/to/folder" # change here

        # define the analysis scenario
        # ------------------------------------------------------
        scenario = "baseline" # change here

        # define layer groups
        # ------------------------------------------------------
        # change "name", "field" and "weight"

        # this user has both vector and raster layers
        group_fisheries = {
            "vectors": [
                {"name": "fisheries_traps", "field": None, "weight": 2 },
                {"name": "fisheries_seines", "field": "intensity", "weight": 3 },
            ],
            "rasters": [
                {"name": "fisheries_gillnets.tif", "weight": 10 },
                {"name": "fisheries_longlines.tif", "weight": 5 },
            ]
        }
        # this user has only vector layers
        group_windfarms = {
            "vectors": [
                {"name": "eolico_linhas_transmissao", "field": None, "weight": 1 },
                {"name": "eolico_torres", "field": None, "weight": 5 },
            ],
        }

        # this user has only raster layers
        group_cargo = {
            "rasters": [
                {"name": "navegacao_densidade.tif", "weight": 1}
            ]
        }
        # setup groups dictionary
        # ------------------------------------------------------
        # define actual names for Ocean Users
        groups = {
            "fisheries": group_fisheries,
            "windfarms": group_windfarms,
            "cargo": group_cargo,
        }

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        output_file = module.setup_users(
            folder_project=folder,
            groups=groups,
            scenario=scenario
        )

        print(" ----- DONE -----")