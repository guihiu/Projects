import  pandas as pd
from io import BytesIO
from shutil import copyfileobj

def eraser(file):
    import os
    if os.path.isfile(file):
        os.remove(file)
    else:
        print("Arquivo não encontrado.")

def save(name, uploaded_file):
    source = getattr(uploaded_file, "stream", uploaded_file)
    source.seek(0)
    with open(name, "wb") as destination:
        copyfileobj(source, destination)
    return True

def create(source, num):
   
    from sdv.metadata import Metadata
    from sdv.single_table import GaussianCopulaSynthesizer

    dados_amostra = pd.read_excel(source)
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
    dados_sinteticos = sintetizador.sample(num_rows=num)["dados"]

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
    generated_file = BytesIO()
    dados_sinteticos.to_excel(generated_file, index=False, sheet_name="Dados")
    generated_file.seek(0)

    return generated_file

if __name__=="__main__":
    fonte="arquivo.xlsx"
    new_file="gerados.xlsx"
    print("ola")
    save(new_file, create(fonte, 20))