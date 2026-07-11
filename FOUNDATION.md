# Base de Dados e Fundação do Projeto

## 1. Base de dados escolhida

**Open Football Database (openfootball)**  
Base de dados pública e de domínio público (Creative Commons Zero - CC0) com resultados de partidas de futebol de múltiplas ligas nacionais, copas continentais e Copa do Mundo, mantida desde 2013 e atualizada continuamente (inclusive com temporadas 2026/27 já em andamento).

- **Site do projeto:** https://openfootball.github.io
- **Organização no GitHub:** https://github.com/openfootball
- **Repositório JSON (o que vamos consumir):** https://github.com/openfootball/football.json
- **Repositório fonte original (Football.TXT):** https://github.com/openfootball/england (e repositórios equivalentes por país: `deutschland`, `espana`, `italy`, `europe`, `worldcup`, etc.)

## 2. Justificativa da escolha

**Pergunta de negócio:**  
*Eficiência emocional*: qual o impacto no desempenho dos times diante de um gol sofrido?  
Como a partida se desenrola a partir do momento em que um time sofre um gol? Existe tendência de resposta (empate/virada) ou os times geralmente não reagem bem?

**Por que essa base resolve esse problema:**
- Traz resultados de partidas de múltiplas ligas e países, permitindo comparar o padrão de "resposta a gol sofrido" entre diferentes campeonatos/culturas de futebol.
- É dado de domínio público (licença CC0), sem custo de acesso e sem necessidade de API key.
- Tem volume histórico relevante (múltiplas temporadas, múltiplas ligas), suficiente para dar significância estatística à análise.

**Quem usaria esse dado na vida real:**
- Departamentos de performance/análise de clubes de futebol (entender como o time reage sob pressão).
- Veículos de mídia esportiva e plataformas de análise esportiva (storytelling orientado a dados, modelagem de probabilidade pós-gol).

**Confiabilidade da fonte:**
- Mantida publicamente no GitHub desde 2013, com atualizações ativas (última atualização documentada inclui temporadas 2026/27).
- Dados dedicados a domínio público. Menção do autor: "*The `football.db` schema, data and scripts are dedicated to the public domain. Use as you please with no restrictions whatsoever.*"
- É referência conhecida na comunidade de dados abertos de futebol (usada em diversos projetos públicos no GitHub).

## 3. Formato dos dados

- **Formato de consumo:** JSON (`football.json`), gerado automaticamente a partir do formato-fonte **Football.TXT**.
- **Exemplo de acesso (raw file):**
  `https://raw.githubusercontent.com/openfootball/football.json/master/2015-16/en.1.json`
- **Estrutura básica de um arquivo JSON de temporada/liga:**

```json
{
  "name": "Premier League 2015/16",
  "matches": [
    {
      "round": "Matchday 1",
      "date": "2015-08-08",
      "team1": "Manchester United",
      "team2": "Tottenham Hotspur",
      "score": { "ft": [1, 0] }
    }
  ]
}
```

#### ⚠️ **Consideração técnica importante para os pipelines:**
> O JSON padrão do `football.json` só traz o **placar final** (`score.ft`), sem o minuto de cada gol. Como a pergunta de negócio depende de saber *o momento em que o time sofreu o gol* e o que aconteceu depois, o JSON puro **não é suficiente sozinho**.
> O formato-fonte **Football.TXT** já traz os gols com minuto e status (pênalti, gol contra), por exemplo:
> `(Neymar 71'; Diego 56')`.  
> Para viabilizar a análise de "resposta pós-gol", o pipeline de ingestão (Bronze) precisará contemplar **também** o parsing dos arquivos `.txt` de origem (ou usar repositórios JSON mais ricos, como o `worldcup.json`, que em alguns torneios trazem eventos com mais detalhe). **Isso deve ser registrado na camada Bronze como enriquecimento necessário.**

## 4. Volume estimado

** *(TODO: info a confirmar com precisão após o uso  efetivo da base. Os valores abaixo são estimativa baseada na cobertura pública do repositório, para fins de dimensionamento inicial do pipeline)* **

- **Escopo proposto:** Múltiplas ligas nacionais europeias (e.g. Inglaterra, Alemanha, Espanha, Itália, França) + Copa do Mundo, cobrindo várias temporadas.
- **Ordem de grandeza:** Dezenas de milhares de partidas no total (cada liga/temporada tem entre ~200 e ~380 jogos; considerando 5 ligas × ~10 temporadas, estimamos algo entre 15.000 e 20.000 partidas).
- **Tamanho em disco:** Pequeno (arquivos JSON de texto simples, cada temporada/liga tipicamente entre poucos KB e ~1 MB), total do escopo proposto deve ficar na casa de dezenas de MB, não exigindo infraestrutura de "big data" pesada, mas sendo suficiente para demonstrar a arquitetura Medallion completa.

## 5. Dicionário de dados

### 5.1 Camada Bronze > dado bruto (estrutura da fonte JSON)

| Campo | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `competition_name` | string | Nome da competição/temporada. vem do campo `name` do arquivo | "Premier League 2015/16" |
| `round` | string | Rodada ou fase da competição | "Matchday 1", "Quarter-finals" |
| `date` | date | Data da partida | 2026-10-12 |
| `team1` | string | Time mandante | "Barcelona" |
| `team2` | string | Time visitante | "Real Madrid" |
| `score_ft_home` | integer | Placar final: gols do mandante | 2 |
| `score_ft_away` | integer | Placar final: gols do visitante | 1 |
| `score_ht_home` | integer (opcional) | Placar do intervalo: gols do mandante | 1 |
| `score_ht_away` | integer (opcional) | Placar do intervalo: gols do visitante | 1 |
| `source_file` | string | Nome/caminho do arquivo de origem (para rastreabilidade/lineage) | "football.json/master/2015-16/en.1.json" |

### 5.2 Enriquecimento necessário (extraído do Football.TXT): eventos de gol

| Campo | Tipo | Descrição |
|---|---|---|
| `match_id` | string | Chave para relacionar com a partida correspondente |
| `team` | string | Time que marcou o gol |
| `scorer` | string | Nome do jogador que marcou |
| `minute` | integer | Minuto do gol (inclui acréscimos, ex.: 90+3) |
| `is_penalty` | boolean | Indica se o gol foi de pênalti |
| `is_own_goal` | boolean | Indica se foi gol contra |

### 5.3 Camada Silver/Gold (visão conceitual, TODO: a refinar)

| Campo | Tipo | Descrição |
|---|---|---|
| `match_id` | string | Identificador único da partida |
| `league` | string | Liga/competição normalizada |
| `season` | string | Temporada normalizada (ex.: "2015-16") |
| `conceding_team` | string | Time que sofreu o gol |
| `goal_minute` | integer | Minuto em que o gol foi sofrido |
| `score_diff_before_goal` | integer | Diferença de placar antes do gol sofrido |
| `final_result` | string | Resultado final da partida (vitória/empate/derrota do time que sofreu o gol) |
| `goals_scored_after_conceding` | integer | Gols marcados pelo time após sofrer o gol analisado |

## 6. Licença e uso

- **Licença:** Creative Commons Zero v1.0 Universal (CC0) / domínio público. Uso livre, sem restrições, sem necessidade de atribuição obrigatória.
- Não há dados sensíveis/pessoais nesta base (não há CPF, endereço ou dado de saúde), apenas dados públicos de resultados esportivos e nomes de jogadores/times, que são informação pública por natureza.
