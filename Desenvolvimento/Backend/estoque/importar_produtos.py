import pandas as pd
from estoque.models import Produto

def importar_planilha():
    df = pd.read_excel('controle epi.xlsx')

    # Elimina linhas sem nome ou sem estoque
    df = df.dropna(subset=['Nome', 'Estoque'])

    produtos_criados = 0

    for _, row in df.iterrows():
        nome = str(row['Nome']).strip()
        try:
            estoque_fisico = int(row['Estoque']) if pd.notna(row['Estoque']) else 0
            estoque_minimo = int(row['Estoque Minimo']) if pd.notna(row['Estoque Minimo']) else 0
            preco_unitario = float(row['Preço Unitario']) if pd.notna(row['Preço Unitario']) else 0.0

            if nome != '' and estoque_fisico >= 0:  # Validação extra
                Produto.objects.create(
                    nome=nome,
                    estoque_fisico=estoque_fisico,
                    estoque_minimo=estoque_minimo,
                    preco_unitario=preco_unitario
                )
                produtos_criados += 1

        except (ValueError, TypeError) as e:
            print(f"❌ Erro na linha: {row.to_dict()} | Erro: {e}")

    print(f"✅ {produtos_criados} produtos importados com sucesso!")
