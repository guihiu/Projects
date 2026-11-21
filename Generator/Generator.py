import  pandas as pd



def apagar(caminho):
    import os
    if os.path.isfile(caminho):
        os.remove(caminho)
        print("Arquivo apagado com sucesso.")
    else:
        print("Arquivo não encontrado.")

def create(novo_file, fonte):
    #codigo Copilot
    from sdv.metadata import Metadata
    from sdv.single_table import GaussianCopulaSynthesizer

    dados_amostra = pd.read_excel(fonte)
    colunas = ["Nome Científico", "CAP cm", "Ht (m)"]

    if not all(coluna in dados_amostra.columns for coluna in colunas):
        raise ValueError(
            "O arquivo deve conter as colunas: Nome Científico, CAP cm e Ht (m)"
        )

    dados_amostra = dados_amostra[colunas].dropna()

    if dados_amostra.empty:
        raise ValueError("A amostra não contém dados válidos.")

    dados_amostra["CAP cm"] = pd.to_numeric(dados_amostra["CAP cm"], errors="coerce")
    dados_amostra["Ht (m)"] = pd.to_numeric(dados_amostra["Ht (m)"], errors="coerce")
    dados_amostra = dados_amostra.dropna(subset=["Nome Científico", "CAP cm", "Ht (m)"])

    if dados_amostra.empty:
        raise ValueError("A amostra não contém valores numéricos válidos.")

    metadata = Metadata.detect_from_dataframes(
        data={"dados": dados_amostra},
    )

    sintetizador = GaussianCopulaSynthesizer(
        metadata=metadata,
        enforce_min_max_values=True,
        enforce_rounding=True
    )
    sintetizador.fit({"dados": dados_amostra})
    dados_sinteticos = sintetizador.sample(num_rows=1000)["dados"]

    dados_sinteticos = dados_sinteticos[colunas]
    dados_sinteticos[["CAP cm", "Ht (m)"]] = dados_sinteticos[
        ["CAP cm", "Ht (m)"]
    ].round(2)
    dados_sinteticos["Nome Científico"] = dados_sinteticos["Nome Científico"].where(
        dados_sinteticos["Nome Científico"].isin(dados_amostra["Nome Científico"].unique()),
        dados_amostra["Nome Científico"].iloc[0]
    )
    dados_sinteticos["CAP cm"] = dados_sinteticos["CAP cm"].clip(
        lower=dados_amostra["CAP cm"].min()
    )
    dados_sinteticos["Ht (m)"] = dados_sinteticos["Ht (m)"].clip(
        lower=dados_amostra["Ht (m)"].min()
    )

    dados_sinteticos = dados_sinteticos.reset_index(drop=True)
    dados_sinteticos.to_excel(novo_file, index=False, sheet_name="Dados")

    return novo_file

fonte="arquivo.xlsx"

df = pd.read_excel(fonte)
print(df.head())
novo_file="gerados.xlsx"

create(novo_file, fonte)