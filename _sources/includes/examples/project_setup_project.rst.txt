.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module file
        # ------------------------------------------------------
        file = "path/to/project.py" # change here

        # define the base folder
        # ------------------------------------------------------
        folder_base = "path/to/folder"  # change here

        # define project name
        # ------------------------------------------------------
        project_name = "narnia"  # change here

        # define scenario names
        # ------------------------------------------------------
        # change here
        scenarios = [
            "baseline",
            "utopia",
            "distopia",
        ]

        # call the function
        # ------------------------------------------------------

        spec = iu.spec_from_file_location("module", file)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        output_file = module.setup_folders(
            name=project_name,
            folder_base=folder_base,
            scenarios=scenarios,
        )

        print(" ----- DONE -----")