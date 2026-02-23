.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module
        # ------------------------------------------------------
        module = "path/to/project.py"

        # define the project folder
        # ------------------------------------------------------
        folder = "path/to/folder"

        # define habitat code/id field
        # ------------------------------------------------------
        field = "code"

        # define habitats grouping scheme for benthic
        # ------------------------------------------------------

        group_benthic = [
            {"name": "coarse", "values": ["MB3", "MC3"]},
            {"name": "infra", "values": ["MB4", "MB5", "MB6"]},
            {"name": "circa", "values": ["MC4", "MC5", "MC6"]},
            {"name": "coarse-off", "values": ["MD3"]},
            {"name": "mix-off", "values": ["MD4", "MD5", "MD6"]},
            {"name": "rock", "values": ["ME1"]},
            {"name": "batial", "values": ["ME4", "MF4", "MF5"]},
            {"name": "abyssal", "values": ["MG4", "MG6"]},
        ]

        # define habitats grouping scheme for pelagic
        # ------------------------------------------------------
        group_pelagic = [
            {"name": "mixed-reduced", "values": ["MH2"]},
            {"name": "fronts-reduced", "values": ["MH7"]},
            {"name": "unstratified", "values": ["MH8"]},
            {"name": "stratified", "values": ["MH9"]},
            {"name": "fronts-full", "values": ["MHA"]},
        ]

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        ls_output = module.setup_habitats(
            folder_project=folder,
            habitat_field=field,
            groups={
                "benthic": group_benthic,
                "pelagic": group_pelagic
            },
        )

        print(" ----- DONE -----")