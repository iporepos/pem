.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module file
        # ------------------------------------------------------
        file = "path/to/conflict.py" # change here

        # define the project folder
        # ------------------------------------------------------
        folder = "path/to/folder" # change here

        # define scenario
        # ------------------------------------------------------
        scenario = "baseline"

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", file)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        output = module.setup_conflict_matrix(
            folder_project=folder,
            scenario=scenario
        )

        print(" ----- DONE -----")