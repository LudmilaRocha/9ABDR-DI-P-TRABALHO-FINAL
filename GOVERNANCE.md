# Governança e Sustentabilidade do Pipeline

## 4.1 Frequência de Atualização

A frequência de atualização do pipeline deve seguir o ritmo natural do dado, não faz sentido rodar o pipeline todo dia se novos dados só aparecem uma vez por semana.

No caso da base *Open Football Database*, os jogos acontecem principalmente entre sexta e domingo, durante a temporada regular (agosto a maio). Cada rodada dura em média uma semana. Isso significa que, na prática, não existe dado novo para coletar entre uma segunda e a próxima sexta-feira.

Por isso, a **frequência escolhida é semanal**: o pipeline roda toda segunda-feira às 06h, coletando todos os jogos da semana anterior. Essa escolha tem três motivos simples:

1. A rodada da maioria das ligas europeias termina no domingo. Na segunda, os dados já estão publicados no repositório.
2. A análise que queremos fazer (como o time reage após sofrer um gol) é estatística e retrospectiva. Não precisamos dos dados em tempo real.
3. Rodar o pipeline com mais frequência só geraria custo sem nenhum dado a mais.

No recesso entre temporadas (junho e julho), o pipeline entra em modo reduzido: uma verificação mensal checa se houve alguma publicação retroativa ou correção na base, mas nenhuma carga completa é executada. Na primeira semana de agosto, retorna ao ritmo semanal.

| Período | Frequência | Quando roda |
|---|---|---|
| Temporada (ago–mai) | Semanal | Toda segunda, 06h |
| Recesso (jun–jul) | Mensal | Primeiro dia do mês, 06h |
| Correções pontuais | Sob demanda | Manual |

---

## 4.2 Política de Expurgo e Retenção

Retenção de dados envolve responder a uma pergunta direta: *vale o custo de guardar isso?*

Três fatores pesam nessa decisão: o custo de armazenamento, o valor que o histórico tem para a análise, e se existe alguma obrigação legal de guardar ou descartar.

Para a base *Open Football Database*, não há obrigação legal (não são dados pessoais nem financeiros). O custo de armazenamento é baixo, a base inteira cabe em dezenas de megabytes, o que é praticamente zero em qualquer nuvem atual. E o valor do histórico é alto: quanto mais temporadas e ligas, mais confiável fica a análise estatística.

Portanto, **a política geral é manter tudo**, com uma distinção entre o que fica em armazenamento rápido (hot) e o que vai para armazenamento frio e mais barato (cold), à medida que o dado envelhece.

**Bronze (dado bruto):**
Os arquivos originais (JSON e TXT) ficam guardados para sempre. Eles são a única forma de reprocessar tudo do zero caso alguma transformação tenha sido feita errado. Como são pequenos e imutáveis, não há razão para apagar. Depois de 24 meses sem acesso, migram para cold storage.

**Silver (dado limpo):**
O dado consolidado fica guardado indefinidamente, é a base para recriar qualquer agregação Gold sem precisar voltar ao Bronze. Versões intermediárias geradas durante migrações de esquema são descartadas 90 dias depois que a migração estiver estável.

**Gold (métricas e agregações):**
A versão atual das métricas fica sempre disponível. Versões antigas (geradas por modelos anteriores) ficam por 12 meses para fins de auditoria e comparação, depois migram para cold storage.

| Camada | O que guardar | Por quanto tempo | Depois disso |
|---|---|---|---|
| Bronze | Arquivos brutos | Indefinido | Cold storage após 24 meses sem acesso |
| Silver | Dado limpo consolidado | Indefinido | — |
| Silver | Versões de migração | 90 dias | Descarte |
| Gold | Versão atual das métricas | Indefinido | — |
| Gold | Versões históricas | 12 meses | Cold storage |

---

## 4.3 Tratamento de Dados Sensíveis

A base *Open Football Database* não tem dados sensíveis. Nomes de jogadores e times são informação pública, e não há CPF, dado de saúde, contrato ou qualquer informação pessoal protegida pela LGPD.

Mesmo assim, o trabalho pede que descrevamos como trataríamos dados sensíveis *se a base os tivesse*. É um exercício válido — pipelines de dados esportivos reais frequentemente incluem informações médicas de atletas, avaliações de desempenho ou dados contratuais, que são sim dados sensíveis e precisam de cuidado.

**O que faríamos em cada etapa:**

**Na entrada do pipeline (Bronze):** campos sensíveis nunca chegariam à plataforma em texto aberto. Antes de qualquer persistência, CPFs, dados de saúde e informações contratuais seriam substituídos por tokens anônimos. O mapeamento entre o token e o valor real ficaria em um cofre externo (como AWS Secrets Manager ou HashiCorp Vault), fora do ambiente de dados e acessível apenas por processos auditados.

Ambas as plataformas têm suporte nativo para isso:
- **Databricks:** Unity Catalog com Column Masks
- **Snowflake:** Dynamic Data Masking Policies

**Na Silver:** dados usados para análise estatística agregada seriam anonimizados de forma irreversível, ou seja, nem com acesso ao banco seria possível recuperar a identidade original. O objetivo é que analistas consigam trabalhar com os padrões sem nunca ter acesso ao indivíduo.

**Controle de acesso por perfil (RBAC):**

| Perfil | Bronze | Silver | Gold |
|---|---|---|---|
| Engenheiro de dados | Acesso total | Acesso total | Acesso total |
| Analista de dados | Sem acesso | Leitura (colunas não sensíveis) | Leitura total |
| Cientista de dados | Sem acesso | Leitura (dados anonimizados) | Leitura total |
| Consumidor de dashboard | Sem acesso | Sem acesso | Leitura total |

Nenhum perfil abaixo de engenheiro de dados acessa o Bronze, que é onde o dado original estaria antes do mascaramento.

**Auditoria:** todo acesso a dado sensível seria registrado: qual usuário, qual processo, em que horário. Isso é feito nativamente pelo Unity Catalog no Databricks e/ou pelo Access History do Snowflake, e é o mínimo esperado de qualquer pipeline que possa conter dados regulados.
