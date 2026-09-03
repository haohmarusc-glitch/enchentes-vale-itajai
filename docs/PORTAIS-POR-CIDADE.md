# Portais de Defesa Civil por cidade — varredura de 03/09/2026

Testado o padrão `https://defesacivil.<cidade>.sc.gov.br/` para as 23 cidades da bacia.

## Resultado: só 5 cidades têm portal próprio
| Cidade | Portal | O que já extraímos |
|---|---|---|
| **Itajaí** | ✅ | 11 réguas + cotas oficiais, marés, barragens, chuvas, `Mapa.php` (coordenadas), 45 abrigos (via ArcGIS) |
| **Blumenau** | ✅ (AlertaBlu) | nível horário, 102 enchentes históricas, risco por bairro, 2.034 cotas de rua (PDF 2014) |
| **Rio do Sul** | ✅ | API Asthon: 27 estações / 21 com nível / 11 com cota, 10 traçados de rio, 23 abrigos com status, 555 cotas de rua |
| **Gaspar** | ✅ | cotas 6/7 (gatilho composto), 69 enchentes 1852–2023, 28 abrigos **com cota própria**, 1.615 cotas de rua |
| **Taió** | ✅ | ⬅️ **NOVO, não explorado** — descoberto nesta varredura |

## As outras 18 NÃO têm portal dedicado
Ituporanga · Ibirama · Ascurra · Apiúna · Indaial · Timbó · Pomerode · Ilhota · Navegantes · Lontras ·
Laurentino · Agronômica · Presidente Getúlio · Doutor Pedrinho · Benedito Novo · Rio dos Cedros ·
Luiz Alves · Rio do Oeste

**Isso explica a estrutura de dependência do projeto:** para essas 18, a única fonte é a **rede estadual**
(GraphQL da Defesa Civil de SC) — que dá nível BRUTO sem cota. É por isso que a regra
`usar_para_cota=false` afeta tantas cidades: não é limitação do coletor, é ausência de fonte municipal.

⚠️ **Ressalva do método:** o teste usou `fetch` em modo `no-cors`, que só diz se o host respondeu — não
distingue "site existe" de "redirecionou para a prefeitura". Pode haver falso negativo (cidade com portal
em outro endereço, ex.: dentro do site da prefeitura, como `cidade.sc.gov.br/defesacivil`). Vale testar
esse segundo padrão.

## O que isso implica
1. **Taió é a próxima fronteira.** É a cabeceira do Itajaí do Oeste, hoje sem cota de rua e com nível
   intermitente. Se o portal tiver cotas ou histórico, fecha uma das lacunas mais antigas.
2. **Para as 18 sem portal, o caminho é o ofício** — não há dado a raspar. Ou a EPAGRI (que classifica em
   faixas do lado dela e cobre a bacia inteira), se liberarem o acesso.
3. **O padrão de qualidade varia muito entre os 5 portais**, e cada um tem algo que os outros não têm:
   - Gaspar: cota por abrigo (único)
   - Rio do Sul: API estruturada com cotas por régua (único)
   - Itajaí: 11 réguas e maré (único)
   - Blumenau: série histórica desde 1852 e cotas de rua com abrigo
   - Não existe formato comum — cada integração é sob medida.

## Próximo passo
Abrir `defesacivil.taio.sc.gov.br` e verificar: cotas de referência, histórico de enchentes, abrigos,
cotas de rua, e se há API. Testar também o padrão `<cidade>.sc.gov.br/defesacivil` para as 18 restantes.
