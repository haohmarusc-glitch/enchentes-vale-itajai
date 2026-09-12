# Certificado intermediário do AlertaBlu

`sectigo-dv-r36.pem` é o certificado público Sectigo Public Server Authentication CA DV R36, emitido pela Sectigo Public Server Authentication Root R46, válido até 21/03/2036. Obtido do endereço AIA do certificado do site: http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt.

O transporte do AIA não é a origem da confiança. O OpenSSL valida a assinatura do intermediário até as raízes do pacote padrão de requests, além da validade e do hostname do servidor. VERIFY_X509_PARTIAL_CHAIN fica desabilitado: o intermediário não é tratado como raiz. Não se usa verify=False. O adaptador é restrito a https://defesacivil.blumenau.sc.gov.br/ e não altera a confiança global do PC ou VPS.

O antigo blumenau.pem continha apenas o certificado final do site (validade até novembro de 2026). Ele não é mais usado pelo coletor. A correção foi testada com resposta HTTP 200 no endpoint oficial e leitura convertida de 2026-09-12T01:00:00Z para 2026-09-11T22:00:00 de Brasília.

Para validar na VPS após atualizar: `python3 scripts/coleta_alertablu.py`. A escolha entre fonte primária e resgate não foi alterada.
