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

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        output_files = module.setup_roi(
            folder_project=folder,
        )

        print(" ----- DONE -----")