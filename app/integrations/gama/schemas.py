from pydantic import BaseModel


class GamaItemRow(BaseModel):
    """Uma linha do JSON achatado do Gama (requirements.md §9).

    Sem envelope: o payload de ingestão é diretamente `list[GamaItemRow]` — não existe cabeçalho
    de pedido separado, os dados do pedido se repetem em cada linha de item.
    """

    ped: str
    item: int
    cnpj_fornecedor: str
    nome_fornecedor: str
    dt_criacao: int
    cod_mat: str
    desc_mat: str
    um: str
    fator_conv: int
    qtd_ped: int | float
    qtd_rec: int | float
    preco_unit_centavos: int
    situacao: int
