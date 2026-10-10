# ArcGIS de Itajaí: o serviço das manchas históricas declara edição pública — 10/10/2026

**Pendência do README:** "O ArcGIS de Itajaí pode estar com ESCRITA aberta ao público — verificar e comunicar".
Até hoje o proxy bloqueava o domínio. Em 10/10/2026 o serviço respondeu.

**Regra seguida:** só leitura da descrição do serviço (`?f=json`), que lista as permissões sem exercer nenhuma.
**Nenhuma escrita foi tentada**, nem de teste: não se testa escrita em serviço de produção alheio.

## O que o serviço declara

`https://arcgis.itajai.sc.gov.br/server/rest/services/historico_inundacoes/FeatureServer`, lido sem login (HTTP 200,
com o `User-Agent` do projeto):

| campo | valor |
|---|---|
| `capabilities` do serviço | **`Query,Create,Update,Delete,Uploads,Editing,Extract`** |
| `capabilities` da camada 0 (área atingida de 1983) | as mesmas |
| `allowGeometryUpdates` | `true` |
| `ownershipBasedAccessControlForFeatures` | ausente (sem regra de "só o autor edita") |
| `hasVersionedData` | `true` |
| `/rest/info` → `authInfo` | `isTokenBasedSecurity: true` (o servidor tem login, mas este serviço abriu sem ele) |

As 10 camadas do serviço:
- áreas atingidas de **1983, 1984, 2001, 2008 e 2011**;
- cotas de **set/2011, jul/2013, set/2013, jun/2014 e out/2015**.

Capturas, com sha256, em `data/brutos/arcgis-itajai-2026-10-10/`:

| arquivo | sha256 |
|---|---|
| `historico_inundacoes-FeatureServer.json` | `56601924…` |
| `historico_inundacoes-FeatureServer-0.json` | `d81f4678…` |
| `rest-info.json` | `584c3f7a…` |

## O que isso quer dizer, e o que não quer

- **Confirmado:** o serviço é lido sem login e anuncia criar, alterar, apagar e enviar arquivos em todas as camadas.
- **Não confirmado, e não vai ser:** se um visitante anônimo consegue de fato gravar. Só uma tentativa de escrita
  provaria, e ela está vetada.
- **Avaliação:** num ArcGIS Enterprise, serviço público com `Editing` habilitado e sem controle por autor costuma
  aceitar edição anônima. Se for o caso, qualquer pessoa pode alterar ou apagar o registro de onde a água chegou em
  1983, 1984, 2001, 2008 e 2011.
- **Para o site:** as manchas que usamos vêm do bruto de 06/09/2026 e não são relidas da origem. Esse bruto passa a
  ser também uma cópia de segurança de um acervo alterável. Mais uma razão para não trocar as nossas manchas pelas de
  lá sem comparar.

## O que falta: comunicar (decisão do Jefferson)

O README pede comunicar ao GEOItajaí/COMPDEC, mas a orientação de 14/09 é **não enviar ofício ao município de
Itajaí**. É um aviso de segurança, não um pedido de dado: o que fazer é decisão sua.

| opção | como |
|---|---|
| a) aviso curto ao GEOItajaí | só o fato: o serviço lido sem login lista `Create, Update, Delete, Editing`. Sem pedir nada e sem link do site |
| b) manter a orientação de 14/09 | não comunicar; o bruto de 06/09 segue como cópia de segurança |

Nenhum texto foi rascunhado nem enviado.
