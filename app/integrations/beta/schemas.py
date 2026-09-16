from pydantic import BaseModel, ConfigDict, Field


class BetaHeaderRow(BaseModel):
    """Uma linha de `cabecalho.csv` (requirements.md §9).

    Todos os campos ficam `str`: é o tipo que `csv.DictReader` sempre entrega. Conversão para
    `Decimal`/`date`/enum é feita pelo adapter (T17), não aqui.
    """

    model_config = ConfigDict(populate_by_name=True)

    numero_pedido: str = Field(alias="NUMERO_PEDIDO")
    fornecedor_cnpj: str = Field(alias="FORNECEDOR_CNPJ")
    fornecedor_razao_social: str = Field(alias="FORNECEDOR_RAZAO_SOCIAL")
    emissao: str = Field(alias="EMISSAO")
    situacao: str = Field(alias="SITUACAO")
    moeda: str = Field(alias="MOEDA")


class BetaItemRow(BaseModel):
    """Uma linha de `itens.csv` (requirements.md §9)."""

    model_config = ConfigDict(populate_by_name=True)

    numero_pedido: str = Field(alias="NUMERO_PEDIDO")
    item: str = Field(alias="ITEM")
    codigo_material: str = Field(alias="CODIGO_MATERIAL")
    descricao: str = Field(alias="DESCRICAO")
    unidade: str = Field(alias="UNIDADE")
    qtd_pedida: str = Field(alias="QTD_PEDIDA")
    qtd_recebida: str = Field(alias="QTD_RECEBIDA")
    preco_unitario: str = Field(alias="PRECO_UNITARIO")
