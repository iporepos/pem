#!/usr/bin/env python3
"""
process_pem_indices.py

Consolida os resultados do PEM (results.gpkg), que trazem uma camada por
escala espacial x cenario (grid_cenario0..3, units_micro_cenario0..3,
units_macro_cenario0..3), em um unico GeoPackage de saida com uma camada
por escala espacial (pem_indices_malha_hex, pem_indices_upg_micro,
pem_indices_upg_macro), onde os cenarios viram colunas no padrao
"{abreviacao}_{cenario}" (<=10 caracteres, conforme Quadro 3 do relatorio
de padronizacao).

Os indices gerais (benefit/conflict/risk/performance) sao consolidados
para os 4 cenarios. Colunas de intensidade de uso do mar por setor
(scenario0_indices no config) sao OPCIONAIS: se essa secao nao existir no
config, essas colunas simplesmente nao entram na saida vetorial (por
exemplo, quando esse dado passa a ser publicado apenas em formato raster).

Alem do GeoPackage, gera:
  - camadas_pem_indices.csv
        1 linha por camada de saida, com os elementos "Obrigatorio" do
        Quadro 2 (Perfil MGB Sumarizado) do relatorio de padronizacao.
  - colunas_{camada}.csv (um por camada de saida, ex. colunas_pem_indices_malha_hex.csv)
        1 linha por coluna, com nome tecnico, alias (nome curto), descricao
        (texto completo) e tipo.
  - LEIAME.txt
        Log da execucao: data/hora, duracao, maquina, config usado e
        descricao de cada arquivo gerado.

Uso:
    python process_pem_indices.py --config config.json
"""

from __future__ import annotations

import argparse
import getpass
import json
import platform
import socket
import sys
import time
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

MAX_COLUMN_CHARS = 10
MAX_LAYER_CHARS = 30


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_config(cfg: dict) -> None:
    """Falha cedo se alguma abreviacao/camada estourar os limites de
    caracteres definidos no relatorio de padronizacao."""
    errors = []

    for scale_key, scale_cfg in cfg["scales"].items():
        layer_name = scale_cfg["output_layer"]
        if len(layer_name) > MAX_LAYER_CHARS:
            errors.append(
                f"Camada de saida '{layer_name}' ({scale_key}) tem "
                f"{len(layer_name)} caracteres (limite: {MAX_LAYER_CHARS})."
            )

    for scen in cfg["scenario_order"]:
        suffix = cfg["scenarios"][scen]
        for name, spec in cfg["general_indices"].items():
            col = f"{spec['short']}_{suffix}"
            if len(col) > MAX_COLUMN_CHARS:
                errors.append(
                    f"Coluna geral '{col}' ({name}, cenario {scen}) tem "
                    f"{len(col)} caracteres (limite: {MAX_COLUMN_CHARS})."
                )

    # scenario0_indices e opcional: colunas de intensidade de uso do
    # cenario base, quando o dado vetorial as inclui. Se ausente no
    # config, essas colunas simplesmente nao entram na saida (ex.: quando
    # a intensidade de uso passa a ser publicada apenas em raster).
    base_suffix = cfg["scenarios"][cfg["scenario_order"][0]]
    for name, spec in cfg.get("scenario0_indices", {}).items():
        col = f"{spec['short']}_{base_suffix}"
        if len(col) > MAX_COLUMN_CHARS:
            errors.append(
                f"Coluna do cenario base '{col}' ({name}) tem "
                f"{len(col)} caracteres (limite: {MAX_COLUMN_CHARS})."
            )

    for key, spec in cfg["id_aliases"].items():
        if key in ("fid", "geometry"):
            continue
        if len(key) > MAX_COLUMN_CHARS:
            errors.append(
                f"Coluna de id '{key}' tem {len(key)} caracteres "
                f"(limite: {MAX_COLUMN_CHARS})."
            )

    if errors:
        raise ValueError(
            "Config invalida - abreviacoes/nomes estouram os limites do "
            "padrao de nomenclatura:\n  - " + "\n  - ".join(errors)
        )


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #

def read_layer(gpkg_path: Path, layer_name: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(gpkg_path, layer=layer_name)
    # 'fid' e o identificador nativo do GeoPackage (gerenciado pelo OGR na
    # escrita); nao deve ser tratado como coluna de dados.
    if "fid" in gdf.columns:
        gdf = gdf.drop(columns=["fid"])
    return gdf


# --------------------------------------------------------------------------- #
# Processamento por escala
# --------------------------------------------------------------------------- #

def process_scale(gpkg_path: Path, scale_cfg: dict, cfg: dict, warnings_log: list[str]):
    prefix = scale_cfg["input_prefix"]
    id_from = scale_cfg["id_column"]["from"]
    id_to = scale_cfg["id_column"]["to"]

    scenarios = cfg["scenario_order"]            # ["0", "1", "2", "3"]
    scenario_suffixes = cfg["scenarios"]          # {"0": "a0", ...}
    scenario_labels = cfg["scenario_labels"]      # {"0": "Baseline...", ...}
    general_cfg = cfg["general_indices"]
    general_order = cfg["general_order"]
    # opcionais: colunas de intensidade de uso do cenario base (ausentes
    # quando esse dado passa a ser publicado apenas em raster)
    scen0_cfg = cfg.get("scenario0_indices", {})
    scen0_order = cfg.get("scenario0_order", [])
    id_aliases = cfg["id_aliases"]

    base_scenario = scenarios[0]
    base_layer = f"{prefix}{base_scenario}"
    gdf_base = read_layer(gpkg_path, base_layer)

    if id_from not in gdf_base.columns:
        raise KeyError(f"Coluna de id '{id_from}' nao encontrada em '{base_layer}'.")
    gdf_base = gdf_base.rename(columns={id_from: id_to})

    out = gdf_base[[id_to, "geometry"]].copy()

    columns_catalog = [{
        "coluna": id_to,
        "alias": id_aliases[id_to]["alias"],
        "descricao": id_aliases[id_to].get("descricao", ""),
        "tipo": id_aliases[id_to].get("type") or str(gdf_base[id_to].dtype),
    }]

    # cache das camadas de cenario ja lidas, para nao reler do disco a cada indice
    scenario_cache: dict[str, gpd.GeoDataFrame] = {base_scenario: gdf_base}

    def get_scenario_gdf(scen: str) -> gpd.GeoDataFrame:
        if scen not in scenario_cache:
            layer_name = f"{prefix}{scen}"
            gdf_s = read_layer(gpkg_path, layer_name)
            if id_from not in gdf_s.columns:
                raise KeyError(f"Coluna de id '{id_from}' nao encontrada em '{layer_name}'.")
            gdf_s = gdf_s.rename(columns={id_from: id_to})
            scenario_cache[scen] = gdf_s
        return scenario_cache[scen]

    # --- indices gerais: presentes em todos os cenarios ---
    for name in general_order:
        spec = general_cfg[name]
        short = spec["short"]
        for scen in scenarios:
            suffix = scenario_suffixes[scen]
            new_col = f"{short}_{suffix}"
            gdf_s = get_scenario_gdf(scen)
            if name not in gdf_s.columns:
                raise KeyError(f"Coluna '{name}' nao encontrada em '{prefix}{scen}'.")
            if scen == base_scenario:
                out[new_col] = gdf_s[name].values
            else:
                merged = out[[id_to]].merge(gdf_s[[id_to, name]], on=id_to, how="left")
                if merged[name].isna().any():
                    msg = (f"{merged[name].isna().sum()} feicao(oes) sem correspondencia de "
                           f"id em '{prefix}{scen}' para '{name}'.")
                    print(f"  aviso: {msg}", file=sys.stderr)
                    warnings_log.append(msg)
                out[new_col] = merged[name].values

            columns_catalog.append({
                "coluna": new_col,
                "alias": f"{spec['alias']} ({suffix.upper()})",
                "descricao": f"{spec['descricao']} — {scenario_labels[scen]}",
                "tipo": spec.get("type", "real"),
            })

    # --- indices exclusivos do cenario base (cenario 0) ---
    base_suffix = scenario_suffixes[base_scenario]
    for name in scen0_order:
        spec = scen0_cfg[name]
        short = spec["short"]
        new_col = f"{short}_{base_suffix}"
        if name not in gdf_base.columns:
            raise KeyError(f"Coluna '{name}' nao encontrada em '{base_layer}'.")
        out[new_col] = gdf_base[name].values
        columns_catalog.append({
            "coluna": new_col,
            "alias": f"{spec['alias']} ({base_suffix.upper()})",
            "descricao": f"{spec['descricao']} — {scenario_labels[base_scenario]}",
            "tipo": spec.get("type", "real"),
        })

    columns_catalog.append({
        "coluna": "geometry",
        "alias": id_aliases.get("geometry", {}).get("alias", "Geometria"),
        "descricao": id_aliases.get("geometry", {}).get("descricao", ""),
        "tipo": str(gdf_base.geom_type.iloc[0]) if len(gdf_base) else "geometry",
    })

    out = gpd.GeoDataFrame(out, geometry="geometry", crs=gdf_base.crs)
    return out, columns_catalog


# --------------------------------------------------------------------------- #
# Catalogo de camadas (Quadro 2 - elementos "Obrigatorio" do Perfil MGB)
# --------------------------------------------------------------------------- #

def build_layer_catalog_row(layer_name: str, cfg: dict, today: str) -> dict:
    catalog_cfg = cfg["layer_catalog"]
    common = catalog_cfg.get("common", {})
    specific = catalog_cfg["layers"].get(layer_name, {})

    row = {"Camada": layer_name}
    for field in catalog_cfg["mandatory_fields"]:
        if field in specific:
            row[field] = specific[field]
        elif field in common:
            row[field] = common[field]
        elif field in ("Data de criação", "Data dos metadados"):
            row[field] = today
        else:
            row[field] = "<AJUSTAR>"
    return row


# --------------------------------------------------------------------------- #
# LEIAME.txt (log da execucao)
# --------------------------------------------------------------------------- #

def build_leiame(
    start_dt: datetime,
    end_dt: datetime,
    elapsed_s: float,
    args_config: Path,
    input_gpkg: Path,
    output_dir: Path,
    output_gpkg_name: str,
    layer_stats: list[dict],
    layer_catalog_name: str,
    warnings_log: list[str],
) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("LOG DE CONSOLIDACAO — pem_indices")
    lines.append("=" * 70)
    lines.append("")
    lines.append("EXECUCAO")
    lines.append("-" * 70)
    lines.append(f"Inicio:            {start_dt.isoformat(sep=' ', timespec='seconds')}")
    lines.append(f"Fim:               {end_dt.isoformat(sep=' ', timespec='seconds')}")
    lines.append(f"Duracao:           {elapsed_s:.2f} s")
    lines.append(f"Usuario:           {getpass.getuser()}")
    lines.append(f"Maquina (host):    {socket.gethostname()}")
    lines.append(f"Sistema:           {platform.platform()}")
    lines.append(f"Python:            {platform.python_version()}")
    lines.append(f"geopandas:         {gpd.__version__}")
    lines.append(f"pandas:            {pd.__version__}")
    lines.append(f"Script:            {Path(__file__).resolve()}")
    lines.append(f"Config utilizado:  {args_config.resolve()}")
    lines.append(f"GeoPackage entrada:{input_gpkg.resolve()}")
    lines.append(f"Diretorio saida:   {output_dir.resolve()}")
    lines.append("")

    lines.append("CAMADAS PROCESSADAS")
    lines.append("-" * 70)
    for stat in layer_stats:
        lines.append(f"- {stat['output_layer']}  (escala: {stat['scale_key']})")
        lines.append(f"    camadas de origem:  {', '.join(stat['source_layers'])}")
        lines.append(f"    feicoes:            {stat['n_features']}")
        lines.append(f"    colunas:            {stat['n_columns']}")
    lines.append("")

    if warnings_log:
        lines.append("AVISOS")
        lines.append("-" * 70)
        for w in warnings_log:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("ARQUIVOS GERADOS")
    lines.append("-" * 70)
    lines.append(f"{output_gpkg_name}")
    lines.append(
        "    GeoPackage consolidado com uma camada por escala espacial "
        "(malha hexagonal H3, UPG micro e UPG macro). Cada camada reune os "
        "4 cenarios de analise (a0-a3) como colunas, seguindo o padrao de "
        "nomenclatura <=10 caracteres definido no relatorio de padronizacao."
    )
    lines.append("")
    lines.append(f"{layer_catalog_name}")
    lines.append(
        "    Catalogo das camadas de saida: 1 linha por camada, com os "
        "elementos de preenchimento obrigatorio do Quadro 2 (Perfil MGB "
        "Sumarizado / ISO 19115) — Titulo, Data de criacao, Credito, "
        "Idioma, Categoria tematica, Descricao, Resumo, Formato de "
        "distribuicao, Sistema de referencia, Responsavel pelos "
        "metadados, Data dos metadados e Status."
    )
    lines.append("")
    for stat in layer_stats:
        lines.append(f"colunas_{stat['output_layer']}.csv")
        lines.append(
            f"    Dicionario de dados da camada '{stat['output_layer']}': 1 linha "
            "por coluna, com nome tecnico (coluna), nome curto (alias), "
            "descricao completa (descricao, incluindo o cenario a que se "
            "refere) e tipo de dado (tipo)."
        )
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Padroniza resultados PEM em pem_indices.gpkg")
    parser.add_argument("--config", required=True, type=Path, help="Caminho do config.json")
    args = parser.parse_args()

    start_dt = datetime.now()
    t0 = time.perf_counter()

    cfg = load_config(args.config)
    validate_config(cfg)

    input_gpkg = Path(cfg["input_gpkg"])
    if not input_gpkg.exists():
        raise FileNotFoundError(f"GeoPackage de entrada nao encontrado: {input_gpkg}")

    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_gpkg = output_dir / cfg["output_gpkg"]
    if output_gpkg.exists():
        output_gpkg.unlink()

    today = date.today().isoformat()
    layer_catalog_rows = []
    layer_stats = []
    warnings_log: list[str] = []

    for scale_key, scale_cfg in cfg["scales"].items():
        print(f"Processando escala '{scale_key}'...")
        out_gdf, columns_catalog = process_scale(input_gpkg, scale_cfg, cfg, warnings_log)

        out_layer_name = scale_cfg["output_layer"]
        out_gdf.to_file(output_gpkg, layer=out_layer_name, driver="GPKG")
        print(f"  -> camada '{out_layer_name}' gravada "
              f"({len(out_gdf)} feicoes, {len(out_gdf.columns)} colunas)")

        cols_csv_path = output_dir / f"colunas_{out_layer_name}.csv"
        pd.DataFrame(columns_catalog).to_csv(cols_csv_path, index=False, encoding="utf-8-sig")
        print(f"  -> catalogo de colunas: {cols_csv_path.name}")

        layer_catalog_rows.append(build_layer_catalog_row(out_layer_name, cfg, today))
        layer_stats.append({
            "scale_key": scale_key,
            "output_layer": out_layer_name,
            "source_layers": [
                f"{scale_cfg['input_prefix']}{s}" for s in cfg["scenario_order"]
            ],
            "n_features": len(out_gdf),
            "n_columns": len(out_gdf.columns),
        })

    layer_catalog_name = "camadas_pem_indices.csv"
    layer_catalog_path = output_dir / layer_catalog_name
    pd.DataFrame(layer_catalog_rows).to_csv(layer_catalog_path, index=False, encoding="utf-8-sig")
    print(f"Catalogo de camadas: {layer_catalog_path.name}")

    end_dt = datetime.now()
    elapsed_s = time.perf_counter() - t0

    leiame_text = build_leiame(
        start_dt=start_dt,
        end_dt=end_dt,
        elapsed_s=elapsed_s,
        args_config=args.config,
        input_gpkg=input_gpkg,
        output_dir=output_dir,
        output_gpkg_name=cfg["output_gpkg"],
        layer_stats=layer_stats,
        layer_catalog_name=layer_catalog_name,
        warnings_log=warnings_log,
    )
    leiame_path = output_dir / "LEIAME.txt"
    leiame_path.write_text(leiame_text, encoding="utf-8")
    print(f"Log: {leiame_path.name}")

    print(f"Concluido em {elapsed_s:.2f}s.")


if __name__ == "__main__":
    main()