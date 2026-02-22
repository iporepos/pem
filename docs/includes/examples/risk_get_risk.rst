.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module file
        # ------------------------------------------------------
        file = "path/to/risk.py" # change here

        # define the project folder
        # ------------------------------------------------------
        folder = "path/to/folder" # change here

        # define scenario
        # ------------------------------------------------------
        scenario = "baseline"

        # define paths to InVEST HRA outputs
        # ------------------------------------------------------
        hra_benthic = "path/to/TOTAL_RISK_Ecosystem**_pelagic.tif"
        hra_pelagic = "path/to/TOTAL_RISK_Ecosystem**_pelagic.tif"

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", file)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        ls_output = module.get_risk_index(
            folder_project=folder,
            scenario=scenario,
            hra_benthic=hra_benthic,
            hra_pelagic=hra_pelagic
        )

        print(" ----- DONE -----")