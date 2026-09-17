# Exemplos de nota fiscal para `POST /invoice-checks`

O desafio não fornece um formato de exemplo pra nota fiscal (só pra pedido de compra) — quem a
envia é a própria V360, não o sistema do cliente. Este arquivo junta exemplos prontos pra colar
no Swagger (`/docs`) ou usar com `curl`, cobrindo os cinco tipos de resultado (conforme + os
quatro tipos de divergência) para os três clientes.

**Pré-requisito**: ingira os três pedidos de exemplo antes de testar (`examples/alfa_payload.json`,
`examples/beta_cabecalho.csv` + `beta_itens.csv`, `examples/gama_payload.json` — veja o README).
Todos os valores abaixo foram conferidos contra esses arquivos exatos; se você alterar os dados de
exemplo, os números aqui deixam de bater.

---

## Alfa — pedido `4500001234`

Item `MAT-1001`: pedido 100, recebido 60, **pendente 40**, preço R$45,90.

### ✅ Conforme
```json
{
  "source_system": "alfa",
  "po_number": "4500001234",
  "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
  "items": [ { "material": "MAT-1001", "quantity": 40, "total_value": 1836.00 } ]
}
```

### ❌ VENDOR_MISMATCH (CNPJ diferente do pedido)
```json
{
  "source_system": "alfa",
  "po_number": "4500001234",
  "vendor": { "tax_id": "99999999000199", "name": "Fornecedor Errado" },
  "items": [ { "material": "MAT-1001", "quantity": 40, "total_value": 1836.00 } ]
}
```

### ❌ MATERIAL_NOT_IN_ORDER (material que não existe no pedido)
```json
{
  "source_system": "alfa",
  "po_number": "4500001234",
  "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
  "items": [ { "material": "MAT-9999", "quantity": 5, "total_value": 100.00 } ]
}
```

### ❌ QUANTITY_EXCEEDS_PENDING (pede 41, só há 40 pendente)
```json
{
  "source_system": "alfa",
  "po_number": "4500001234",
  "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
  "items": [ { "material": "MAT-1001", "quantity": 41, "total_value": 1881.90 } ]
}
```

### ❌ PRICE_MISMATCH (esperado R$1.836,00, veio R$2.000,00)
```json
{
  "source_system": "alfa",
  "po_number": "4500001234",
  "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
  "items": [ { "material": "MAT-1001", "quantity": 40, "total_value": 2000.00 } ]
}
```

---

## Beta — pedido `20260088412`

Item `MAT-77`: pedido 1.200, recebido 400, **pendente 800**, preço R$6,49. CNPJ do fornecedor
funciona mascarado ou não (`"12.345.678/0001-90"` ou `"12345678000190"`).

### ✅ Conforme
```json
{
  "source_system": "beta",
  "po_number": "20260088412",
  "vendor": { "tax_id": "12.345.678/0001-90", "name": "Distribuidora Horizonte Ltda" },
  "items": [ { "material": "MAT-77", "quantity": 800, "total_value": 5192.00 } ]
}
```

### ❌ VENDOR_MISMATCH
```json
{
  "source_system": "beta",
  "po_number": "20260088412",
  "vendor": { "tax_id": "99999999000199", "name": "Fornecedor Errado" },
  "items": [ { "material": "MAT-77", "quantity": 800, "total_value": 5192.00 } ]
}
```

### ❌ MATERIAL_NOT_IN_ORDER
```json
{
  "source_system": "beta",
  "po_number": "20260088412",
  "vendor": { "tax_id": "12345678000190", "name": "Distribuidora Horizonte Ltda" },
  "items": [ { "material": "MAT-999", "quantity": 5, "total_value": 100.00 } ]
}
```

### ❌ QUANTITY_EXCEEDS_PENDING (pede 801, só há 800 pendente)
```json
{
  "source_system": "beta",
  "po_number": "20260088412",
  "vendor": { "tax_id": "12345678000190", "name": "Distribuidora Horizonte Ltda" },
  "items": [ { "material": "MAT-77", "quantity": 801, "total_value": 5198.49 } ]
}
```

### ❌ PRICE_MISMATCH (esperado R$5.192,00, veio R$6.000,00)
```json
{
  "source_system": "beta",
  "po_number": "20260088412",
  "vendor": { "tax_id": "12345678000190", "name": "Distribuidora Horizonte Ltda" },
  "items": [ { "material": "MAT-77", "quantity": 800, "total_value": 6000.00 } ]
}
```

---

## Gama — pedido `GL-778`

Depois da conversão de unidade (`CX` → `UN`): item `TRP-01` fica 120 pedido / 24 recebido /
**pendente 96**, preço R$100,00; item `TRP-09` fica 12 pedido / 0 recebido / **pendente 12**,
preço R$33,333... (dízima — `100 ÷ 3`, ver `design.md` §4.4). A nota é sempre em unidades, nunca
em caixas.

### ✅ Conforme (`TRP-01`, divisão exata)
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "34567890000112", "name": "Transportes Ideal ME" },
  "items": [ { "material": "TRP-01", "quantity": 96, "total_value": 9600.00 } ]
}
```

### ✅ Conforme (`TRP-09`, prova que a dízima não gera falso `PRICE_MISMATCH`)
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "34567890000112", "name": "Transportes Ideal ME" },
  "items": [ { "material": "TRP-09", "quantity": 12, "total_value": 400.00 } ]
}
```

### ❌ VENDOR_MISMATCH
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "99999999000199", "name": "Fornecedor Errado" },
  "items": [ { "material": "TRP-01", "quantity": 96, "total_value": 9600.00 } ]
}
```

### ❌ MATERIAL_NOT_IN_ORDER
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "34567890000112", "name": "Transportes Ideal ME" },
  "items": [ { "material": "TRP-99", "quantity": 5, "total_value": 100.00 } ]
}
```

### ❌ QUANTITY_EXCEEDS_PENDING (pede 97, só há 96 pendente — já em unidades)
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "34567890000112", "name": "Transportes Ideal ME" },
  "items": [ { "material": "TRP-01", "quantity": 97, "total_value": 9700.00 } ]
}
```

### ❌ PRICE_MISMATCH (esperado R$9.600,00, veio R$15.000,00)
```json
{
  "source_system": "gama",
  "po_number": "GL-778",
  "vendor": { "tax_id": "34567890000112", "name": "Transportes Ideal ME" },
  "items": [ { "material": "TRP-01", "quantity": 96, "total_value": 15000.00 } ]
}
```
