# Plano aprovado — nova página de Progresso

Aprovado pelo Francisco em 2026-11-12. **✅ EXECUTADO em 2026-11-12**, tudo em `index.html`.
Falta só a tua aprovação final e o commit.

## O que mudou em relação ao plano, e porquê

1. **Janelas de 30 dias em vez de "este mês vs mês passado".** No dia 12 do mês, comparar
   um mês a meio com um mês inteiro dava sempre uma queda enorme e falsa (−57% no teste).
   O resumo e o cartão de comparação passaram a "últimos 30 dias vs os 30 dias anteriores".
2. **Um valor de 0 passou a contar como "não se aplica", não como zero.** Sem isto, os dips
   feitos sem peso apareciam como uma linha rente ao chão e só depois saltavam. Agora esses
   treinos ficam de fora da métrica e o gráfico diz quantos foram.
3. **Corrigido um defeito antigo do HTML:** só o `#overview` está dentro do `.content`, por
   isso todas as outras abas ficavam coladas às margens e com 94 px de espaço vazio no topo.
   A Progress passou a ter o mesmo contentor, e o espaço vazio foi removido em todas as abas
   (o `.content` passa a esconder-se quando o Overview não está à vista). As outras abas
   continuam coladas às margens — não lhes toquei, está fora do combinado.
4. **A Progress passou a redesenhar-se quando os dados do gist chegam**, caso já estejas
   nessa aba à espera.
5. Apagadas as regras CSS dos gráficos antigos, que ficaram sem uso.

## Ajustes pedidos depois de ver a página (2026-11-12)

- **Fora a duração média** do resumo. Ficam 3 números: treinos, volume, recordes.
- **"Todos os exercícios" subiu** para antes de "Evolução por exercício" — é a secção
  mais usada.
- **A tabela tem o seu próprio seletor 3M / 6M / 12M / Tudo** (começa em 3M, guardado
  em `fp-pr-list-range`). A seta de cada linha passou a ser a diferença entre o primeiro
  e o último treino **do período escolhido**, não entre os dois últimos treinos.
- **Grupos musculares como etiquetas coloridas** na tabela: Ombros azul, Peito roxo,
  Pernas verde, Glúteos âmbar, Braços rosa, Core azul-petróleo (classes `.mgt-*`).
- **Exercícios com o mesmo nome passaram a ser o mesmo exercício**, em qualquer dia do
  plano (`exBaseName` / `exGroup` / `exListGrouped`). O sufixo "(Day X)" é ignorado.
  - **Progress:** uma linha só por exercício (19 → 17). `exPoints` e `legacyMonthly`
    juntam os treinos de todas as chaves do grupo, cada set com o seu próprio ×1/×2.
  - **Training:** `saveW` e `setMult` escrevem em todas as chaves do grupo, e `lastSets`
    procura o último treino do exercício em qualquer dia.
  - Grupos atuais: `Lateral Raises` = `wC-1` + `wD-lat` · `Leg Press` = `wB-lp` + `wB-2`.
  - Não houve migração de dados: nada foi reescrito no gist. Os treinos antigos de cada
    chave continuam lá e aparecem juntos por leitura.
- **Treinos esquecidos fecham-se sozinhos** (`autoCloseStaleWorkout`, `AUTO_CLOSE_MS` = 1 h).
  Corre ao abrir a app, ao voltar a ela (`visibilitychange`, `focus`) e depois de o gist
  carregar — nunca antes, para não escrever por cima do gist com dados pela metade
  (`gistReady`). Fecha quando passou 1 h desde o início **e** 1 h desde a última mexida
  no rascunho (`workoutDraft.touch`), para não cortar um treino longo a meio.
  A sessão fica marcada com `auto: true` e a barra do dia mostra "(automático)".
  Se não houver nenhum set registado, o rascunho é deitado fora em vez de gravar vazio.
- **O treino passou a contar para o dia em que começou**, não para o dia em que foi
  gravado (`isoDate(new Date(startISO))` em vez de `todayStr()`). Isto também arranja o
  caso de um treino que atravessa a meia-noite.
- **A aba Training passou a saber registar exercícios sem peso** (`inputMode`), usando
  os mesmos três tipos da Progress:
  - `kg` — `[peso] × [reps]`, rodapé "Volume total: X kg" (como antes).
  - `bw` — só `[reps]` com a unidade ao lado, rodapé "Total: X reps", e um botão
    **"+ peso"** (`addWeightToBw`, flag `fp-wk-<key>`, válida para todo o grupo) que
    revela a coluna dos quilos. Passa a `kg` sozinho assim que houver peso registado.
  - `tempo` — só `[segundos]`, rodapé "Tempo total: X s". Os segundos continuam a ser
    guardados no campo `w` com `r: "1"` e `mult: 1`, que é como a Progress já os lê.
  - Os campos que não se aplicam ficam no DOM mas escondidos por CSS (`.mode-bw`,
    `.mode-tempo`), para `readRows` / `effW` / `isTouched` não partirem.
  - Nos exercícios sem peso esconde-se também o campo de kg e o ×1/×2 da linha
    (`.ex.no-weight`), e a etiqueta "última:" passa a mostrar `s` ou `reps`.
- **Peso máx passou a ser a métrica por omissão** em vez do 1RM estimado (`metricsFor`).
  O 1RM continua disponível como botão. Nota para o futuro: como o Francisco progride
  sobretudo em repetições, o Peso máx vai mostrar linhas planas em exercícios onde ele
  está mesmo a evoluir — o botão 1RM é que mostra essa subida.

---

Ficheiro alterado: `index.html` (ficheiro único). Secção `#progress`
e o bloco de gráficos em JS.

---

## Decisões já tomadas (não voltar a perguntar)

1. **"Diferença de peso" = peso levantado nos exercícios.** Não é peso corporal.
2. **Histórico antigo:** desenhar como **linha esbatida, um ponto por mês**, só para os
   meses **anteriores ao primeiro treino gravado** (ou seja, até 2026-09 inclusive).
   De 2026-10 em diante manda a linha real, vinda de `sessions`. Nada é apagado do gist.
3. **Os 19 gráficos pequenos saem** e são substituídos por: lista de exercícios com
   mini-linha + **um** gráfico grande com seletores.
4. **Withings fica de fora.** Não há credenciais no `.env`, não há dados guardados,
   e a app não tem código que os leia. Projeto separado, se algum dia.

---

## Fontes de dados — o que é verdade e o que não é

### `gistData.sessions` — **única fonte fiável**
Escrito só em `finishWorkout()`. 7 treinos, 19 out → 7 nov 2026.
Por treino: `date`, `day`, `start`, `end`, `vol`, `exercises[key].sets[] = {w, r, vol}`, `mult`.
Só **10 dos 19 exercícios** aparecem, com 1–3 pontos cada. Nove estão a zero.

### `gistData.history` — contaminado antes de 2026-11-09
O campo de peso escrevia no histórico em quase todos os dias em que a app era aberta,
mesmo sem treino (16 exercícios × 72 datas, das quais só 7 são treinos reais).
A maioria dos exercícios tem **1 ou 2 valores distintos em 7 meses** — não há curva
escondida ali. Usar **apenas** como a linha esbatida da decisão 2.

### ⚠️ Regra que não se quebra
**Nunca escrever em `gistData.history` fora de `applySessionToHistory()`.**
Foi exactamente esse o defeito corrigido em `f0c39b2`. Todos os gráficos novos
leem de `sessions`; o `history` é só de leitura.

### Dados sujos a tratar
- **Durações:** 2 dos 7 treinos têm 735 min e 3351 min (esqueceu-se de acabar), outro
  tem 0,9 min. Ignorar sessões com duração > 3 h ou < 2 min em qualquer média de duração.
- **`vol` por set** não serve para Plank (segundos) nem para exercícios sem peso.

---

## Métrica certa por exercício

O campo "peso" não quer sempre dizer kg. Tabela a criar (19 linhas), a usar em
todos os gráficos, recordes e no 1RM estimado.

**Três tipos:**
- **`kg`** — peso × reps normal. 1RM estimado, volume, peso máximo.
- **`bw`** — peso do corpo. Mostra **repetições** enquanto o peso dos sets for 0 ou vazio,
  e **passa sozinho a kg** (com 1RM estimado e volume) assim que ele começar a registar
  peso > 0 nesse exercício. Decidido assim porque o Francisco quer poder passar a fazer
  dips com pesos no futuro, e o mesmo pode acontecer aos outros `bw`.
  Nunca forçar reps-only de forma fixa nestes.
- **`tempo`** — segundos. Nem kg nem 1RM; mostra segundos máximos e total.

| Exercício | chave | tipo | nota |
|---|---|---|---|
| Dumbbell OHP | `wC-0` | kg | mult 2 |
| Lateral Raises | `wC-1` | kg | mult 2 |
| Rear Delt Fly | `wD-2` | kg | mult 2 |
| **Face Pulls** | `wD-fp` | **bw** | sem peso "pelo menos atualmente". O campo tem 15 guardado mas os sets reais são 0/0/1 kg — o 15 pode ser limpo |
| Bench Press | `wA-bench` | kg | |
| **Push-ups** | `wA-pushup` | **bw** | placeholder "BW", campo vazio |
| Barbell Back Squat | `wB-0` | kg | mult 2 |
| Romanian Deadlift | `wB-1` | kg | mult 2 |
| Hip Thrust | `wB-4` | kg | mult 2 |
| Glute Step Downs | `wB-sd` | kg | mult 2 |
| Leg Press | `wB-lp` | kg | |
| Barbell Bicep Curl | `wD-0` | kg | mult 2 |
| Hammer Curls | `wD-1` | kg | mult 2 |
| Skull Crushers | `wC-3` | kg | |
| **Tricep Dips** | `wC-dip` | **bw** | confirmado: fez com peso do corpo, o **20 guardado foi erro** e pode ser limpo. Quer passar a fazer com pesos mais à frente — por isso `bw` e não reps-only, para mudar sozinho quando ele puser peso |
| Lateral Raises (D) | `wD-lat` | kg | |
| Leg Press (D) | `wB-2` | kg | |
| **Hanging Leg Raises** | `wA-6` | **kg** | confirmado: pesos no tornozelo. 2 kg × mult 2 = 4 kg |
| **Plank** | `wC-5` | **tempo** | placeholder "— s", valor 60. O `mult 2` é lixo aqui, ignorar |

---

## A página, de cima para baixo

### Essencial

**A. Resumo do mês**
Treinos feitos, volume total, recordes novos, comparação com o mês anterior.
Dados: `sessions`. ✔ Funciona já.

**B. Consistência — treinos por semana, últimas 12 semanas**
Barras simples, uma linha de altura. Dados: datas de `sessions`. ✔
É a métrica mais honesta com 3 semanas de dados.

**C. Um gráfico grande (~260 px) com três seletores**
- **Exercício** — qual mostrar.
- **Métrica** — peso máximo · **1RM estimado (por omissão)** · melhor set · volume total.
- **Intervalo** — 3M / 6M / 12M / tudo. Manter o seletor Semana/Mês que já existe
  (`setProgressGranularity`, chave `fp-progress-gran` no localStorage).

**1RM estimado, fórmula de Epley:** `(peso × mult) × (1 + reps / 30)`.
Razão de ser: o Francisco progride em **repetições**, não em peso. Nos dados dele,
Skull Crushers passaram de 24 kg × 12 para 24 kg × 22 — e o gráfico atual mostra isso
como uma linha **perfeitamente plana**. O 1RM estimado é o que torna esse progresso visível.

Só **um** `Chart` em vez de 19 → também fica mais rápido no telemóvel.

**D. Lista de exercícios com mini-linha**
Por linha: nome, valor atual, diferença, mini-linha de tendência. Toque abre no gráfico C.
Substitui a visão geral que os 19 gráficos davam.

**E. Recordes por exercício**
Peso máximo, melhor set (kg × reps), 1RM estimado mais alto, melhor sessão — com data.
✔ Funciona desde o primeiro treino. Melhor relação valor/dados de toda a página.

### Bom ter

**F. Cartões de diferença 3 / 6 / 12 meses, com setas (estilo Apple Fitness Trends)**
Fazer os espaços agora; desbloqueiam sozinhos quando houver dados.
Reais hoje: "desde o início" e "vs mês anterior".
3 meses → ~jan 2027 · 6 meses → ~abr 2027 · 12 meses → ~out 2027.
Os que ainda não dão aparecem a cinzento com "faltam X semanas". **Nunca** calcular
uma diferença de 3 meses a partir de 3 pontos.

**G. Volume por grupo muscular**
Peito, pernas, ombros, braços, core. As etiquetas já estão no HTML (`<span class="tag tb">`),
é passá-las para a mesma tabela de 19 linhas.

**H. Métrica certa por tipo de exercício** — a tabela acima.

### Enfeite / mais tarde
Mapa de calor anual (precisa de ~1 ano) · streaks e medalhas · peso corporal e gordura
(Withings, bloqueado) · comparar dois exercícios no mesmo gráfico.

---

## Como testar

O browser da sessão **não consegue ler o gist** sem o token do Francisco.

**Modo de demonstração:** abrir com `?demo=1` carrega um conjunto de treinos falsos de
12 meses para `gistData`, **só em memória**.

- `pushToGist()` tem de ficar **bloqueado** neste modo — sem excepções.
- Os dados falsos devem incluir: exercícios com muitos pontos e exercícios a zero,
  um mês sem treinos nenhuns, sets de peso/reps/segundos, e durações absurdas,
  para testar os casos todos.
- Incluir **um exercício `bw` que começa sem peso e passa a ter peso a meio**
  (caso dos dips), para confirmar que o gráfico muda de repetições para kg sem
  partir a linha nem o histórico.
- Verificar: aspeto a 375 px de largura, os 3 intervalos cheios **e** vazios,
  os cartões de 3/6/12 meses nos dois estados, a linha esbatida a juntar-se à real
  em 2026-10, e os exercícios sem dados.
- Fora de `?demo=1`, nada muda.

---

## Expectativa honesta (dizer ao Francisco se ele perguntar)

Com 7 treinos, o gráfico grande terá 2–3 pontos na maioria dos exercícios e 9 ficam
vazios. O que vale **hoje** é A (resumo), B (consistência) e E (recordes). O gráfico
grande vale por estar pronto a encher: por **janeiro** terá ~3 meses de dados reais.
Os cartões de 6 e 12 meses só servem em **abril** e **outubro de 2027**.

---

## Referências consultadas

- Hevy — [estatísticas por exercício](https://help.hevyapp.com/hc/en-us/articles/35382889578135-Exercise-Performance-Tracking-in-Library-Weight-Bodyweight-Cardio-and-Duration-Based-Exercises) · [recordes pessoais](https://help.hevyapp.com/hc/en-us/articles/35649367857175-Personal-Records-PRs-and-Set-Records-Explained-How-They-Work-in-the-Hevy-App)
- Strong — [gráfico grande com seletor de métrica, 1RM por Epley](https://setgraph.app/ai-blog/best-app-to-track-weight-lifting-progress-top-options-2026)
- Apple Fitness — [Trends](https://support.apple.com/en-lamr/guide/iphone/iph4c34a8a95/16.0/ios) · [como as setas funcionam](https://www.macworld.com/article/3429077/ios-13-and-apple-watch-activity-trends-give-you-the-big-picture.html)
- Whoop — [vistas de tendências](https://whoop.com/thelocker/track-progress-with-new-trend-views)
