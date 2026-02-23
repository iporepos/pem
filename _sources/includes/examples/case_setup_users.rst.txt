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

        # define the analysis scenario
        # ------------------------------------------------------
        scenario = "baseline"

        # define layer groups
        # ------------------------------------------------------

        # -----------------------------------
        group_tourism = {
        "vectors": [
        {
            "name": "turismo_atividades_esportivas",
            "weight": 1
        },{
            "name": "turismo_bares",
            "weight": 5
        },{
            "name": "turismo_esportes_nauticos",
            "weight": 10
        },{
            "name": "turismo_hoteis",
            "weight": 1
        },{
            "name": "turismo_infra_sul",
            "weight": 5
        },{
            "name": "turismo_mergulho_autonomo",
            "weight": 10
        },{
            "name": "turismo_mergulho_livre",
            "weight": 1
        },{
            "name": "turismo_recifes_artificiais",
            "weight": 5
        },
        ]}

        # -----------------------------------
        group_fishing_industry = {
        "rasters": [
        {
            "name": "pesca_driting_longlines.tif",
            "weight": 1
        },{
            "name": "pesca_gillnets.tif",
            "weight": 1
        },{
            "name": "pesca_pole_and_line.tif",
            "weight": 1
        },{
            "name": "pesca_pots_and_traps.tif",
            "weight": 1
        },{
            "name": "pesca_purse_seines.tif",
            "weight": 1
        },{
            "name": "pesca_set_longlines.tif",
            "weight": 1
        },
        ]}

        # -----------------------------------
        group_fisheries_artisans = {
        "vectors": [
        {
            "name": "pesca_artesanal_colonias",
            "weight": 5
        },{
            "name": "pesca_artesanal_comunidades",
            "weight": 5
        },
        ],
        "rasters": [
        {
            "name": "pesca_artesanal_intensidade.tif",
            "weight": 1
        },
        ]}

        # -----------------------------------
        group_aquaculture = {
        "vectors": [
        {
            "name": "aquacultura_associacoes",
            "weight": 1
        },{
            "name": "aquacultura_sinau",
            "weight": 5
        },
        ]}

        # -----------------------------------
        group_windfarms = {
        "vectors": [
        {
            "name": "eolico_linhas_transmissao",
            "weight": 1
        },{
            "name": "eolico_parques",
            "weight": 5
        },{
            "name": "eolico_torres",
            "weight": 10
        },
        ]}

        # -----------------------------------
        group_cargo = {
        "vectors": [
        {
            "name": "navegacao_portos",
            "weight": 5
        },{
            "name": "navegacao_area_porto",
            "weight": 5
        },{
            "name": "navegacao_bacias_evolucao",
            "weight": 5
        },{
            "name": "navegacao_fundeadouros",
            "weight": 5
        },
        ],
        "rasters": [
        {
            "name": "navegacao_densidade.tif",
            "weight": 1
        },
        ]}

        # -----------------------------------
        group_oil = {
        "vectors": [
        {
            "name": "petroleo_plataformas",
            "weight": 5
        },{
            "name": "petroleo_terminais",
            "weight": 5
        },{
            "name": "petroleo_pocos",
            "weight": 4
        },{
            "name": "petroleo_campos_producao",
            "weight": 3
        },{
            "name": "petroleo_blocos_concessao",
            "weight": 2
        },
        ],
        "rasters": [
        {
            "name": "petroleo_densidade_navios.tif",
            "weight": 1
        },
        ]}

        # -----------------------------------
        group_minerals = {
        "vectors": [
        {
            "name": "mineracao_processos",
            "weight": 5
        },{
            "name": "mineracao_areas_potenciais",
            "weight": 5
        },
        ]}

        # -----------------------------------
        # group_defense = {...} # -- todo

        # setup groups dictionary
        # ------------------------------------------------------
        # define actual names for Ocean Users
        groups = {
            "tourism": group_tourism,
            "fishing-industry": group_fishing_industry,
            "fishing-artisans": group_fisheries_artisans,
            "windfarms": group_windfarms,
            "minerals": group_minerals,
            "oil-gas": group_oil,
            "cargo": group_cargo,
            "aquiculture": group_aquaculture,
            # defense: group_defense -- todo
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