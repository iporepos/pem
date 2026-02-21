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

        # define habitat code/id field
        # ------------------------------------------------------
        field = "code"

        # define habitats grouping scheme for benthic
        # ------------------------------------------------------

        group_benthic = [
            {"name": "benthic_a", "values": ["MB3", "MC3"]},
            {"name": "benthic_b", "values": ["MB4", "MB5", "MB6"]},
            {"name": "benthic_b", "values": ["MC4", "MC5", "MC6"]},
            {"name": "benthic_c", "values": ["MD3"]},
            {"name": "benthic_d", "values": ["MD4", "MD5", "MD6"]},
            {"name": "benthic_e", "values": ["ME1"]},
            {"name": "benthic_f", "values": ["ME4", "MF4", "MF5"]},
            {"name": "benthic_f", "values": ["MG4", "MG6"]},
        ]

        # define habitats grouping scheme for pelagic
        # ------------------------------------------------------
        group_pelagic = None  # if None, habitats are not grouped.

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