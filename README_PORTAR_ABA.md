# Portar "My Fitness Plan" para uma aba de outro app de treino

> **Para a LLM que vai ler isto:** a tua tarefa é recriar, como **uma única aba** dentro de outro app de treino, todas as funcionalidades da web app "My Fitness Plan" (este repositório). Este documento descreve tudo o que a app faz, os dados que ela guarda, as regras exatas de cada cálculo, e como cada função chegou ao estado atual (incluindo os erros que já foram corrigidos e não devem voltar). Usa a stack e os componentes do app de destino. Não é preciso copiar o HTML. O que tem de se manter igual é o comportamento e os dados.

Fontes usadas para escrever este documento (todas neste repositório):

- `index.html`: a app inteira (HTML + CSS + JS num só ficheiro, ~1950 linhas).
- Histórico git: 45 commits, de 2026-04-04 a 2026-10-18 (os commits de backup automático foram ignorados).
- `backups/gist-weights.json`: cópia diária dos dados reais do utilizador.
- `PLAN.md` / `REHAB.md`: plano escrito pelo agente `/personal-trainer`. **Atenção:** estão desatualizados em relação ao `index.html` (o split foi reorganizado em 2026-09-08). Para a aba, a fonte de verdade é o `index.html`.

---

## 1. Resumo da app atual

| Item | Valor |
|---|---|
| Tipo | Página única, mobile-first, usada no iPhone como "app" no ecrã inicial |
| Stack | HTML + CSS + JavaScript sem framework |
| Bibliotecas | Chart.js 4.4.0 (gráficos), SortableJS 1.15.2 (arrastar para reordenar) |
| Imagens | [free-exercise-db](https://github.com/yuhonas/free-exercise-db) via `raw.githubusercontent.com`, mais 3 pictogramas locais em `icons/mobility/` |
| Persistência | `localStorage` (cache imediato) + **GitHub Gist** `weights.json` (fonte de verdade, sincronizado entre dispositivos) |
| Backup | GitHub Action diária que copia o gist para `backups/gist-weights.json` |
| Idioma da UI | Inglês na maior parte; as funções mais recentes (sets, sessões, gráficos) estão em português de Portugal |
| Utilizador | Homem, 35 anos, 72 kg, 168 cm, ~21% de gordura, recomposição corporal durante 3 meses, tendinopatia de Aquiles bilateral, risco de hiperextensão do joelho |

A app tem 7 secções (tabs no topo). Na app de destino isto vira **uma aba** com 7 sub-secções (segmented control, sub-tabs ou lista, conforme o padrão do app):

1. ◎ Overview
2. ◑ Progress
3. ▲ Training
4. 🧘 Flexibility
5. 🦵 Achilles
6. ⚡ Power
7. ◇ Nutrition

Por cima de tudo há um cabeçalho fixo com o título, o perfil (`Male · 35 · 72kg · 168cm · ~21% BF`), as tags `Recomp` e `3 months` e um **indicador de sincronização** (ver §4.4).

---

## 2. Funcionalidades, secção a secção

### 2.1 Overview (conteúdo estático)

**Card "3-Month Goals"**: lista de metas no formato *atual → alvo*:

| Ícone | Meta | Descrição | Atual | Seta | Alvo |
|---|---|---|---|---|---|
| 🔥 | Body Fat | Lose fat through recomp — slight deficit + high protein | ~21% | ↓ | 18–19% |
| 💪 | Muscle Mass | Build lean mass with progressive overload on the 4-day split | ~56kg LBM | ↑ | +2kg LBM |
| ⚖️ | Scale Weight | Maintain — recomp means fat out, muscle in | 72kg | → | ~72kg |
| 🏃 | Return to Running | Gradual return via Achilles protocol | Paused | → | 20min pain-free |
| 🧘 | Mobility & Injury Resilience | Daily 10-min routine — shoulder, Achilles & knee focus | Never | → | Daily habit |
| 😴 | Sleep Consistency | Your #1 lever for training consistency — protect it | 6–7h | → | 7.5h |

**Card "Weekly Schedule"**: uma linha por dia. Os dias de descanso aparecem com opacidade 0.45.

| Dia | Sessão | Linha secundária |
|---|---|---|
| Mon | Day A — Shoulders + Chest | + 🧘 mobility · 🏃 cardio (walk/bike/run) · 🦵 Achilles daily |
| Tue | Day C — Arms | idem |
| Wed | Rest *(descanso)* | idem |
| Thu | Day B — Legs & Glutes | idem |
| Fri | Day D — Shoulders + Quads + Core | idem |
| Sat | Cardio (30 min, low-impact) + tag "Outdoors" | + 🧘 mobility · 🦵 Achilles daily |
| Sun | Full Rest *(descanso)* | idem |

Nota de rodapé: *"Cardio is daily now — walk, bike, or run, your pick. Achilles work is also daily, strength day or not. On weeks with 2 gym days: move Day B to Sat. Always prioritize Day A & B at the gym."*

**Card "Injury & Risk Flags"** (alertas a âmbar):
- 🦵 **Achilles Tendinopathy**: No jump rope, no running yet. Eccentric calf protocol only.
- 🦿 **Knee Hyperextension Risk**: Never lock out knees on squats, leg press, or lunges. Leg extension machine removed from plan.

### 2.2 Training (a parte interativa principal)

Quatro cards colapsáveis, **Day A, B, C, D**, todos fechados ao abrir a app. Cada card tem:

1. **Barra de treino** no topo: botão `▶ Começar treino` / `■ Acabar treino` e um texto de estado (ver §2.3).
2. Subtítulo, por exemplo "3 sets each · near failure".
3. Lista de **linhas de exercício**.
4. Botão `+ Add exercise` no fim, que abre um formulário inline.

No fim da secção há um card estático **"Daily Cardio"** (Brisk Walking 20–30 min; Stationary Bike / Cycling, Zone 2, 20–30 min; Running, só pelo protocolo do Aquiles).

#### Anatomia de uma linha de exercício

```
[✓ seleção]   [thumb 76px]   ▸ Nome  [tag músculo]  [vol. total do dia]    [ kg  ]
[⠿ arrastar]                 nota / cue técnico                             [▼][▲]
                                                                            [×1|×2]
───────── painel de sets (expandível, largura total) ─────────
Set 1  [kg] × [reps]                    250 kg   (−)
Set 2  [kg] × [reps]                    250 kg   (−)
[+ Set]                              Volume total: 500 kg
```

| Elemento | Comportamento |
|---|---|
| **Círculo de seleção ✓** ("Doing today") | Liga/desliga. Se **pelo menos um** exercício do dia está ligado, os não selecionados ficam com opacidade 0.3 e descem para o fim da lista. Os selecionados sobem para o topo e cada grupo mantém a ordem relativa. Se nenhum está ligado, nada fica esbatido. O estado persiste (local + gist) e **não é limpo automaticamente** no dia seguinte. |
| **Pega de arrastar ⠿** | Fica por baixo do círculo de seleção. Só a pega inicia o arrasto, para não chocar com os inputs. Ao largar, grava a ordem do dia. Tem de funcionar com toque no iOS (ver §5). |
| **Thumbnail** | Imagem `0.jpg` do exercício. Ao tocar, abre um modal em ecrã inteiro com a `1.jpg` (a posição final do movimento). Toque fora fecha. Se a imagem falhar, esconde-se. |
| **Nome + caret ▸/▾** | Tocar no bloco do nome/nota abre ou fecha o **painel de sets**. |
| **Badge de volume** | Volume total desse exercício no treino em curso (vazio se for 0). |
| **Campo kg** ("peso de trabalho") | Texto livre: aceita `27,5` ou `27.5`, segundos (`60`) para a prancha, e placeholder `— kg`, `BW` ou `— s`. Grava com debounce de 1,2 s. |
| **Stepper ▼▲** | −0,5 / +0,5 no campo kg, arredondado a 0,1, nunca abaixo de 0. Serve para ajustar sem abrir o teclado. |
| **Toggle ×1 / ×2** | Multiplicador de volume. ×2 é para exercícios com dois halteres ou de um lado de cada vez. Afeta todos os cálculos de volume. |
| **Botão apagar ×** | Existe no código mas está **escondido** (`display:none`) desde que o modo de edição foi removido. Se for ativado, pede confirmação. Os exercícios base são apagados de forma *soft* (a key vai para `deleted[]`) e os custom são removidos de `custom[]`. Na aba nova: oferece apagar, por exemplo com swipe e confirmação. |

#### Adicionar exercício (custom)

Formulário inline com: **Nome*** (obrigatório), **Grupo muscular** (por defeito "Custom") e **Notas**. Ao gravar:
- key = `custom-<Date.now()>`
- fica guardado em `custom[]` com `{day, key, name, tag, notes, tagColor:'tp'}` (tag roxa)
- aparece com tudo o que os exercícios base têm: seleção, arrastar, stepper, ×1/×2 e painel de sets.

### 2.3 Sets, volume e sessões de treino (função mais recente, 2026-10-18)

**Painel de sets.** É construído só quando é aberto pela primeira vez (lazy):
- Se houver um **rascunho** para esse exercício, mostra as linhas do rascunho.
- Senão, cria *N* linhas, com *N* = número de sets da **última sessão gravada** desse exercício, ou 3 se não houver nenhuma.
  - Peso pré-preenchido com o valor do campo kg. Se estiver vazio, usa o peso do set correspondente na última sessão.
  - Reps ficam vazias e o **placeholder** mostra as reps desse mesmo set na última sessão. Assim o utilizador vê o que fez da última vez.
- `+ Set` acrescenta uma linha com o peso da linha anterior e o placeholder de reps da última sessão para esse índice.
- `−` remove a linha e renumera as restantes. Se for a única linha, só limpa as reps.
- Cada linha mostra o volume do set. O rodapé mostra o "Volume total".
- Teclados: peso com `inputmode="decimal"`, reps com `inputmode="numeric"`, e fonte de 16px para o iOS não fazer zoom.

**Fórmulas** (iguais em todo o lado):

```
parseNum(v)   = float(v com ',' trocada por '.'); NaN → 0
setVol(w,r,m) = round1(parseNum(w) × parseNum(r) × m)        // m = 1 ou 2
total         = round1(Σ setVol dos sets)
round1(x)     = Math.round(x*10)/10
fmtVol(n)     = round1(n) com separador de milhares " " (ex.: "1 250.5")
```

**Rascunho.** Tudo o que se escreve nos sets é gravado logo em `localStorage['fp-session-draft']`:

```json
{ "day": "A" | null, "start": "ISO" | null, "sets": { "<key>": [ {"w":"25","r":"8"}, ... ] } }
```

Só ficam no rascunho os exercícios com pelo menos um set com reps > 0. O rascunho sobrevive a recarregar a página e a fechar a app.

**Começar / Acabar treino** (um treino de cada vez):
- `▶ Começar treino` em Day X guarda `day = X` e `start = agora`. O botão passa a `■ Acabar treino` (âmbar) e o texto mostra "em curso desde HH:MM". Os botões dos outros dias ficam desativados, com o texto "Treino do Dia X em curso".
- `■ Acabar treino`:
  1. Percorre as linhas do dia que estão **visíveis e não esbatidas** (não apagadas e não marcadas como "skip") e cujo painel já foi aberto.
  2. Por exercício, junta os sets com reps > 0, cada um como `{w, r, vol}`, e calcula `vol` do exercício e `mult`.
  3. Se nenhum exercício tiver sets, mostra o alerta *"Preenche as repetições de pelo menos um set antes de acabar o treino."* e não grava nada.
  4. Cria a sessão `{date:'YYYY-MM-DD', day, start, end, vol, exercises:{key:{mult, sets, vol}}}` e acrescenta-a a `sessions[]`.
  5. Atualiza `history[key][date]` = **peso máximo** usado nesse exercício nesse dia (somando todas as sessões do dia).
  6. Guarda também uma cópia em `localStorage['fp-sessions']` (últimas 200), para o caso de a sincronização falhar.
  7. Limpa o rascunho desses exercícios, reconstrói os painéis abertos e envia para o servidor sem debounce.
- Sem treino em curso, se já existir uma sessão gravada **hoje** para esse dia, o texto mostra: `Gravado ✓ HH:MM · N exercícios · V kg`.

**Reconciliação ao arrancar** (`mergeLocalSessions`): as sessões em `localStorage['fp-sessions']` cujo `end` não existe no servidor são acrescentadas. A lista é ordenada por `end`, o histórico é atualizado e é agendado um envio. `end` (timestamp ISO) funciona como ID da sessão.

### 2.4 Progress

- Card de topo com a explicação: *"Cada gráfico mostra o peso máximo (verde) e o volume máximo num set (âmbar) por semana ou mês."* Tem também um toggle **Week | Month** (por defeito Month), guardado em `localStorage['fp-progress-gran']`.
- Quatro cards colapsáveis (Day A–D) com um gráfico de linha por exercício, na mesma ordem e com os mesmos nomes da secção Training.
- Os gráficos são (re)desenhados ao abrir a secção, ao mudar a granularidade e depois de cada sincronização bem-sucedida.

**Dados de cada gráfico (exercício `key`):**

- Série **peso**: pares `[data, parseNum(history[key][data])]` com valor > 0.
- Série **volume**: para cada sessão que contém `key`, o `[data, maior setVol entre os sets]` (com o `mult` da sessão).
- **Agrupamento**: cada data vai para um período e fica o **máximo** do período (não a média):
  - Semana: chave = segunda-feira da semana ISO (`YYYY-MM-DD`), rótulo `DD/MM`.
  - Mês: chave = `YYYY-MM`, rótulo `Oct '26` (abreviaturas em inglês).
- Eixo X: união dos períodos das duas séries, por ordem. Onde não há valor fica `null`, com `spanGaps: true`.

**Aspeto:**
- Peso: linha verde `#0f7f56` com preenchimento `rgba(15,127,86,0.08)`, eixo Y à esquerda, `suggestedMin = max(0, mínimo − 5)`.
- Volume (só se houver sessões): linha âmbar `#c77d0a` sem preenchimento, **segundo eixo Y à direita** (`suggestedMin 0`, sem grelha).
- `tension 0.3`. Pontos de raio 4 (peso) ou 3 (volume), e 5 se houver só um período. A legenda só aparece se houver série de volume. Tooltip: `"Peso máx: 25 kg"`.
- Altura do gráfico: 120px.
- **Recordes** no cabeçalho de cada exercício: `Máx 32.5 kg · Vol. máx/set 650 kg`, calculados sobre todos os dados e não por período.
- **Estado vazio**: caixa tracejada com *"No history yet — log a workout first"*.

> Lacuna atual: os exercícios **custom** não têm gráfico, porque os canvases estão escritos à mão no HTML. Na aba nova, gera os gráficos a partir da lista real de exercícios de cada dia, incluindo os custom e respeitando a ordem e as remoções.

### 2.5 Flexibility

Seis cards (estilo roxo), cada um uma secção reordenável: **Priority — do these first**, **Shoulders**, **Chest**, **Arms**, **Back & Torso**, **Legs**. Cada linha tem:

- círculo de seleção roxo ("Doing today"), com a mesma lógica de esbater e subir os selecionados do Training, mas aplicada **por card**
- pega de arrastar (a reordenação é por card e grava `mobOrder[cardId]`)
- thumbnail de 72px que abre o modal
- nome, tag roxa e badge **▶** que abre uma pesquisa ou vídeo no YouTube num separador novo
- descrição e dose (por exemplo "30s each")

Não tem campo de peso nem sets.

### 2.6 Achilles

1. Card âmbar fixo: *"Achilles Rehab — Daily, Non-Negotiable. Every day, AM + PM where noted. Consistency is the treatment — not intensity."*
2. Cinco cards colapsáveis com o conteúdo do protocolo:

| Card | Conteúdo |
|---|---|
| **Phase 1 · Isometrics** | Isometric calf holds, 5×45s, todos os dias. *How:* subir ao topo de um calf raise e manter, sem movimento. *Why first:* os isométricos reduzem a dor do tendão mais depressa e não acrescentam carga excêntrica. Pode correr em paralelo com a fase 2. |
| **Phase 2 · Eccentric Calf Raises** | 3×15 num degrau, 2× por dia (AM + PM), 6–12 semanas. Subir com os dois pés e descer em 3 s só com a perna afetada. Semanas 1–2: descida bilateral. Semanas 3–6: descida unilateral alternada. *Gate para a fase 3:* dor ≤2/10 em 5 sessões seguidas e 25+ calf raises numa perna de cada lado. |
| **Phase 3 · Weighted Calf Raises** | HSR 3×8 com carga tolerável, 3 s a subir e 3 s a descer, amplitude completa. Aumentar a carga de semana para semana conforme a dor. |
| **Phase 4 · Plyometrics / Jumps** | Só quando correr não doer. Três linhas **interativas** (seleção, arrastar, thumb, ▶): Broad Jump (com o RDL), Vertical Jump (depois do agachamento), Box Jump (a partir de 30 cm e sempre a descer a pé). 3–5 reps cada. |
| **Return · Return-to-Run Protocol** | Só depois de 1 semana sem dor. Sem. 5–6: walk 3 / jog 1 × 5 (1×/sem). Sem. 7: 2/2 × 5 (1×/sem). Sem. 8: 1/3 × 5 (2×/sem). Sem. 9–10: 20 min contínuos a 6 min/km. Sem. 11: repetir e confirmar 2 sessões sem dor. Sem. 12: 20 min a ritmo confortável ✅, 2×/sem a partir daí. *Stop rule:* dor >3/10 durante ou depois, ou dorido mais de 24 h no dia seguinte → voltar uma fase atrás. |

### 2.7 Power

Card de introdução: *"3–4 sets × 3–5 reps. Move explosively — speed is the load. Pick one, takes 5 min. Trains the power pillar without touching the Achilles. Do it before Day A or Day D, or as its own short session."* Seguem-se três linhas interativas, iguais às da Flexibility: Medicine Ball Chest Pass, Band-Resisted Punch / Light DB Push Press, Plyo Push-ups (Knees OK).

### 2.8 Nutrition

Grelha de 4 macros: **Calories** 1,900–2,000 kcal/day · **Protein** 140–150g (~2g/kg BW) · **Carbs** 180–200g (Around training) · **Fats** 60–70g (Quality sources). Subtítulo: *"Slight deficit + high protein — build muscle while losing fat."*

---

## 3. Catálogo de exercícios (seed)

### 3.1 Keys ≠ dia: atenção

As keys (`wC-0`, `wD-2`…) vêm do split original de abril. Em setembro os exercícios **mudaram de dia, mas as keys ficaram iguais** para não perder o histórico. Por isso `wC-0` (Overhead Press) está no **Day A**. **Não derives o dia a partir da key.** Usa o campo `day` do seed ou o `order` gravado. Se renomeares as keys, o histórico importado deixa de bater certo.

Imagens: `https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/<path>`. O modal usa o mesmo caminho com `/1.jpg` no lugar de `/0.jpg`.

### 3.2 Training

| Dia | key | Nome | Tag | Nota | Placeholder | Imagem (`0.jpg`) |
|---|---|---|---|---|---|---|
| A | `wC-0` | Dumbbell Overhead Press | Shoulders | Priority lift. 20kg. | — kg | `Dumbbell_Shoulder_Press` |
| A | `wC-1` | Lateral Raises (Wall) | Shoulders | 12kg. Lead with elbow, not hand — this is the width that reads athletic, not bulky. | — kg | `Alternating_Deltoid_Raise` |
| A | `wD-2` | Rear Delt Fly (Dumbbells) | Rear Delts | 15kg. Hinge forward 45°, lead with elbows. | — kg | `Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench` |
| A | `wD-fp` | Face Pulls (Cable/Band) | Rear Delts | Pull to face, elbows high and wide. External rotation at end range. Key for shoulder longevity. | — kg | `Face_Pull` |
| A | `wA-bench` | Bench Press | Chest | Progress from 25kg. Control descent, full ROM. | — kg | `Barbell_Bench_Press_-_Medium_Grip` |
| A | `wA-pushup` | Push-ups | Chest | Bodyweight alt to Bench Press — no barbell needed. | BW | `Pushups` |
| B | `wB-0` | Barbell Back Squat | Quads + ⚠ Knee (tag âmbar) | Priority lift. 32.5kg. Stop just before lockout — protect knee hyperextension. | — kg | `Barbell_Squat` |
| B | `wB-1` | Romanian Deadlift | Hips/Lower Back | 34–37kg. Hinge at hip, feel hamstring stretch. | — kg | `Romanian_Deadlift` |
| B | `wB-4` | Hip Thrust | Glutes/Hips | 32.5kg. Squeeze glutes at top for 1s. | — kg | `Barbell_Hip_Thrust` |
| B | `wB-sd` | Glute Step Downs | Glutes/Quads | Step box or bench, lower under control on one leg until heel taps floor, drive back up. Replaces Reverse Lunges. | — kg | `Step-up_with_Knee_Raise` |
| B | `wB-lp` | Leg Press | Quads | Knee-safe quad volume after the squat. | — kg | `Leg_Press` |
| C | `wD-0` | Barbell Bicep Curl | Biceps | Priority lift. 24kg. No swinging. Full extension at bottom. | — kg | `Barbell_Curl` |
| C | `wD-1` | Hammer Curls | Biceps | 20kg. Works brachialis for arm thickness. | — kg | `Alternate_Hammer_Curl` |
| C | `wC-3` | Skull Crushers | Triceps | 18kg. Keep elbows vertical, control descent. | — kg | `EZ-Bar_Skullcrusher` |
| C | `wC-dip` | Tricep Dips | Triceps | BW or add weight. Elbows back, lower until upper arms parallel. Control the descent. | BW | `Dips_-_Triceps_Version` |
| D | `wD-lat` | Lateral Raises | Shoulders | Second shoulder hit of the week — light weight, strict form. | — kg | `Alternating_Deltoid_Raise` |
| D | `wB-2` | Leg Press | Quads | Knee-safe quad volume — second leg hit of the week alongside Day B's squat. | — kg | `Leg_Press` |
| D | `wA-6` | Hanging Leg Raises | Core | Controlled, no swinging. | — kg | `Hanging_Leg_Raise` |
| D | `wC-5` | Plank | Core | Squeeze glutes and abs throughout. | — s | `Plank` |

Títulos e subtítulos dos dias: **A** "Shoulders + Chest" · "3 sets each · near failure"; **B** "Legs & Glutes" · "3 sets each · near failure"; **C** "Arms" · "4 exercises · 3 sets each · near failure"; **D** "Shoulders + Quads + Core" · "4 exercises · 3 sets each · near failure".

Nomes curtos usados nos gráficos de Progress: Dumbbell OHP, Lateral Raises, Rear Delt Fly, Face Pulls, Bench Press, Push-ups, Barbell Back Squat, Romanian Deadlift, Hip Thrust, Glute Step Downs, Leg Press, Barbell Bicep Curl, Hammer Curls, Skull Crushers, Tricep Dips, Lateral Raises, Leg Press, Hanging Leg Raises, Plank.

### 3.3 Flexibility, Power e Achilles Phase 4

As imagens que começam por `icons/` são PNG locais deste repositório e **têm de ser copiadas** para o app de destino. As outras vêm da free-exercise-db.

| Card | id | Nome | Tag | Dose | Imagem | Descrição |
|---|---|---|---|---|---|---|
| Priority | `mob-f-hinge` | Rotational Hinge | Hips/Spine | 8 ea side | `icons/mobility/rotational-hinge.png` | Stand tall, hinge at the hips while rotating the torso toward one leg, reach the opposite hand to the shin. Alternate sides. |
| Priority | `mob-f-hang` | Dead Hangs | Shoulders/Grip | 3×20–30s | `One_Handed_Hang` | Hang from the pull-up bar, full relaxed extension, decompress shoulders and spine. Decompression, not a strength set. |
| Priority | `mob-f-wgs` | World's Greatest Stretch | Full Body | 6–8 ea side | `Worlds_Greatest_Stretch` | Lunge forward, foot outside hand. Drop forearm to floor, rotate arm toward ceiling, hold 1s. |
| Priority | `mob-f-dsq` | Deep Squat | Hips/Ankles | 60s | `Bodyweight_Squat/1.jpg` | Feet shoulder-width, toes out. All the way down, heels flat, knees out. Breathe at the bottom. |
| Priority | `mob-f-ng` | Nerve Glides | Neural | 10 ea side | `icons/mobility/nerve-glides.png` | Straighten one leg, flex foot toward shin, hold 2s, then point — rhythmically. |
| Priority | `mob-f-sst` | Supine Spinal Twist | Spine | 30–45s ea | `Knee_Across_The_Body` | Lie on back, pull one knee to chest, let it fall to the opposite side. Shoulders stay flat. |
| Priority | `mob-f-thor` | Thoracic Rotation | Spine | 10 ea side | *(sem imagem)* | Keep hips still. Hand behind head, rotate upper back only — elbow leads to the ceiling. |
| Shoulders | `mob-f-er` | External Rotation (Band) | Shoulder | 2×12 ea | `External_Rotation_with_Band` | Elbow pinned at side, rotate outward against light band. |
| Shoulders | `mob-f-xs` | Cross-Body Shoulder Stretch | Rear Delts | 30s each | `Shoulder_Stretch/1.jpg` | Pull arm across chest. Shoulder pressed down, not shrugged. |
| Chest | `mob-f-pec` | Pec Stretch (Doorframe) | Chest | 30s each | `Behind_Head_Chest_Stretch` | Arm at 90°, lean forward gently. Shoulder relaxed down. |
| Arms | `mob-f-tri` | Triceps Overhead Stretch | Triceps | 30s each | `Triceps_Stretch/1.jpg` | Arm up, elbow behind head, press elbow down with the other hand. Core braced. |
| Back & Torso | `mob-f-lat` | Doorframe Lat Stretch | Back | 30s each | `One_Arm_Against_Wall` | Grip frame at shoulder height, shift weight back and sit into it. |
| Back & Torso | `mob-f-cc` | Cat-Cows | Spine | ×8 | `Cat_Stretch` | On hands and knees, alternate cow/cat, 2–3s hold each. |
| Back & Torso | `mob-f-child` | Child's Pose | Back/Hips | 60s | `Childs_Pose` | Breathe deeply, decompress lower back, open hips. |
| Legs | `mob-f-couch` | Couch Stretch | Hips | 45s each | `Standing_Elevated_Quad_Stretch` | Knee on pad, foot up wall. Tuck pelvis, push hips forward. Lean back further each week. |
| Legs | `mob-f-coss` | Cossack Squat | Hips | 5 ea side | `icons/mobility/cossack-squat.png` | Wide stance, shift to one side and sink. Aim deeper each week. |
| Legs | `mob-f-pig` | Pigeon Pose / Figure-4 | Glutes | 45s each | `Piriformis-SMR` | Shin forward across the body, sink hips. If knees protest, do supine figure-4. |
| Legs | `mob-f-ham` | Standing Hamstring Stretch | Hamstrings | 30s each | `Standing_Hamstring_and_Calf_Stretch` | Heel on low step, leg straight, hinge with a flat back. |
| Legs | `mob-f-ankle` | Ankle Circles + Dorsiflexion | Achilles | 30s/ankle | `Ankle_Circles` | Slow circles, then flex/point. Finish with loaded dorsiflexion, knee over toes. |
| Power | `mob-power-0` | Medicine Ball Chest Pass | Power | 3–4×3–5 | `Medicine_Ball_Chest_Pass` | 1–2m from wall, explosive chest pass, catch and repeat. |
| Power | `mob-power-1` | Band-Resisted Punch / Light DB Push Press | Power | 3–4×3–5 ea | `One-Arm_Kettlebell_Push_Press` | Band at chest height, punch explosively. Or 5–8kg DB in one sharp hip-assisted pop. |
| Power | `mob-power-2` | Plyo Push-ups (Knees OK) | Power | 3–4×3–5 | `Chest_Push_multiple_response` | Controlled descent, explode up so hands leave the floor. Knees-down counts. |
| Achilles P4 | `mob-later-1` | Broad Jump | Phase 4 (âmbar) | 3–5 reps | `Front_Box_Jump` | Pair with RDL on Day B. Explode forward, land soft, reset fully. |
| Achilles P4 | `mob-later-2` | Vertical Jump (Squat Pairing) | Phase 4 | 3–5 reps | `Freehand_Jump_Squat` | After Day B squat sets, 3–5 explosive vertical jumps. |
| Achilles P4 | `mob-later-3` | Box Jump | Phase 4 | 3–5 reps | `Box_Jump_Multiple_Response` | Start at 30cm. Land on both feet, step down (never jump down). |

IDs dos contentores reordenáveis (chaves de `mobOrder`): `mob-card-flex-priority`, `mob-card-flex-shoulders`, `mob-card-flex-chest`, `mob-card-flex-arms`, `mob-card-flex-back`, `mob-card-flex-legs`, `mob-power-card`, `mob-later-card`.

Links ▶ do YouTube: quase todos são pesquisas `https://www.youtube.com/results?search_query=<nome+do+exercício+tutorial>`. Os mapeamentos exatos estão em `YT_LINKS` no `index.html`. `mob-f-dsq` e `mob-f-ng` apontam ambos para o mesmo vídeo (`watch?v=WL6VSc5XQ-8`), o que provavelmente é um erro em `mob-f-ng`. Confirma com o utilizador.

---

## 4. Modelo de dados

### 4.1 Documento remoto (`weights.json` no Gist)

Um único objeto JSON, com chaves planas mais algumas coleções:

```jsonc
{
  // peso de trabalho atual (string, pode ter vírgula decimal: "27,5")
  "w-<key>": "25",
  // multiplicador de volume: "1" | "2"
  "m-<key>": "2",
  // "doing today" no Training / na mobilidade: "1" | "0"
  "sel-<key>": "1",
  "mob-sel-<rowId>": "0",

  // peso por dia: history[key]["YYYY-MM-DD"] = "25" (string)
  "history": { "wA-0": { "2026-04-04": "25", "...": "..." } },

  // sessões de treino completas (desde 2026-10-18)
  "sessions": [
    { "date": "2026-10-18", "day": "A",
      "start": "2026-10-18T17:02:11.000Z", "end": "2026-10-18T17:55:40.000Z",
      "vol": 3120,
      "exercises": {
        "wC-0": { "mult": 2, "vol": 1200,
                  "sets": [ { "w": "20", "r": "10", "vol": 400 }, "..." ] } } }
  ],

  // exercícios criados pelo utilizador
  "custom": [ { "day": "A", "key": "custom-1776166834487", "name": "Inclined Bench Press",
                "tag": "Chest", "notes": "", "tagColor": "tp" } ],

  // keys de exercícios base apagados (soft delete)
  "deleted": [ "wB-3" ],

  // ordem por dia (Training) e por card (mobilidade)
  "order":    { "A": ["wC-0","wC-1","wD-2","wA-bench","wD-fp","wA-pushup","custom-..."], "B": [...], "C": [...], "D": [...] },
  "mobOrder": { "mob-card-flex-priority": ["mob-f-hinge", "..."], "...": [...] }
}
```

Os dados reais estão em `backups/gist-weights.json` (cerca de 1700 linhas, histórico desde 2026-04-04). Há chaves de exercícios antigos que já não estão na UI (`wA-0`…`wA-5`, `wB-3`, `wB-5`, `wC-2`, `wC-4`, `wD-3`…`wD-5`). **Importa o ficheiro inteiro e não percas essas chaves.** São histórico. Também há 3 exercícios custom. O backup de hoje ainda não tem `sessions`, porque a funcionalidade é de 2026-10-18.

### 4.2 Armazenamento local (`localStorage`)

| Chave | Conteúdo |
|---|---|
| `gh-token` | Token do GitHub, pedido com `prompt()` na primeira vez |
| `fp-w-<key>`, `fp-m-<key>` | Cache do peso e do multiplicador |
| `fp-sel-<key>`, `fp-mob-sel-<id>` | Cache da seleção "doing today" |
| `fp-session-draft` | Rascunho do treino em curso (§2.3) |
| `fp-sessions` | Cópia local das últimas 200 sessões (rede de segurança) |
| `fp-progress-gran` | `week` / `month` |

Todos os acessos ao `localStorage` estão em `try/catch` (ver §5).

### 4.3 Sincronização

- **Ao arrancar:** pinta primeiro com o cache local, para mostrar logo os valores, e depois faz `GET https://api.github.com/gists/<id>` com `Authorization: token <t>`. Quando a resposta chega, aplica pesos, multiplicadores e seleções, depois remoções, depois custom, depois ordem e ordem da mobilidade, e por fim reconcilia as sessões locais.
- **Ao gravar:** faz `PATCH` do ficheiro inteiro com `{files:{'weights.json':{content: JSON.stringify(gistData,null,2)}}}`. Edições normais (peso, ×1/×2, seleção) esperam 1,2 s de debounce. Ações estruturais (acabar treino, reordenar, adicionar ou apagar exercício) enviam logo.
- **Efeito colateral importante:** cada envio regista em `history[key][hoje]` todos os exercícios com o campo kg preenchido. O valor é o peso máximo das sessões de hoje, se existirem, ou o valor do campo, se não existirem. Ver §6.
- Na aba nova: se o app de destino tiver backend próprio, usa-o, mas **mantém o mesmo esquema** para poder importar e exportar o `weights.json`. Se não tiver, mantém o Gist.

### 4.4 Indicador de sincronização (cabeçalho)

`loading…` (cinzento) → `synced ✓` (verde). Ao editar mostra `saving…` (âmbar). Os erros possíveis são `sync failed` (âmbar), `offline — saved locally` / `offline` (cinzento) e `no token — not saved` (âmbar).

---

## 5. Como cheguei a estas funções (histórico e decisões)

Cada função nasceu de um pedido concreto do utilizador, e várias tiveram de ser corrigidas depois. Segue a ordem pelo histórico git, com o porquê de cada decisão. As lições em **negrito** são requisitos para a aba nova.

**Abril 2026: base (2026-04-04 / 05)**
1. *Initial fitness plan page*: o plano era só texto (metas, split de 4 dias, nutrição, hábitos).
2. *Gist sync*: o utilizador treina com o telemóvel e queria os pesos iguais em todos os dispositivos sem montar um backend. Um Gist privado com um JSON chegou. O `localStorage` serve de cache para a página abrir logo.
3. *Progress tab com Chart.js*: para ver progressão, cada gravação passou a escrever `history[key][data]`.
4. *Thumbnails*: primeiro eram botões do YouTube, depois passaram a fotos reais da free-exercise-db, porque se percebe o exercício sem sair da app.
5. *Adicionar e apagar exercícios*: exercícios custom no gist e remoções *soft* (lista `deleted`), para nunca perder histórico. Depois veio a reordenação com botões ▲▼.

**Maio 2026: reequilíbrio (2026-05-10 / 12)**
6. Plano reduzido, mobilidade revista e botão "Edit exercises" removido (os controlos ficaram sempre visíveis). Foi aqui que o botão de apagar ficou escondido.
7. **Os caminhos de imagem têm de ser verificados um a um.** Nomes adivinhados (`Standing_Hamstring_Stretch`…) davam 404.
8. Foi criado o agente `/personal-trainer`, que mantém `PLAN.md` e `REHAB.md` com dados da Withings e do Strava (`fetch_withings.py`, `fetch_strava.py`). Estes scripts **não fazem parte da web app** e não precisam de ser portados.

**Setembro 2026: reestruturação e usabilidade no iPhone (2026-09-08 / 10)**
9. Split reorientado para ombros e braços. Mobilidade, Aquiles e potência passaram para as suas próprias tabs, o cardio passou a diário e a tab Habits desapareceu. Os exercícios mudaram de dia **mantendo as keys** (§3.1).
10. **As imagens têm de mostrar o movimento certo.** Uma revisão encontrou 7 fotos erradas: o Deep Squat mostrava uma torção, o Plank mostrava um Dead Bug, e assim por diante. Nalguns exercícios o frame `0.jpg` é só a pessoa de pé, por isso usa-se o `1.jpg`. Para três exercícios que não existem na base foram desenhados pictogramas próprios.
11. **Arrastar para reordenar tem de funcionar com toque no iOS Safari.** O drag-and-drop nativo do HTML5 não funciona lá, por isso entrou o SortableJS com uma pega dedicada, para não chocar com o checkbox e os inputs.
12. **Todos os acessos a storage ficam em try/catch.** Uma exceção no `getToken()` a meio de um arrasto deixava o Sortable bloqueado até recarregar a página.
13. **Espaço horizontal no telemóvel é o recurso mais escasso.** O ×1/×2 foi para baixo do campo kg, os thumbnails cresceram de 44 para 76 px e a pega foi para baixo do checkbox.
14. **Stepper de ±0,5 kg** para ajustar o peso sem abrir o teclado.
15. **Backup diário** do gist via GitHub Actions, porque o GitHub não garante quanto tempo guarda as revisões do gist.

**Outubro 2026: análise (2026-10-14 / 18)**
16. Gráficos agrupados por **semana ou mês**, porque um ponto por sessão era ruído. Primeiro usou-se a média.
17. **Ícone no ecrã inicial do iOS:** o `apple-touch-icon` vai embutido como *data URI* PNG 180×180 opaco. Com um URL normal, o iPhone mostrava só uma letra, porque o pedido do ícone não chega ao servidor da tailnet.
18. **Sets, sessões e volume** (a função mais recente). O utilizador quis registar cada set (peso × reps), ver o volume e ter "Começar/Acabar treino". Decisões tomadas:
    - Os gráficos passaram da média para o **máximo** por período, porque a média escondia os recordes.
    - Segunda série com o **volume máximo num set**, num eixo próprio porque a escala é muito diferente.
    - Os sets vêm pré-preenchidos e as reps da última sessão aparecem como placeholder, para comparar com a última vez sem ocupar espaço.
    - O rascunho vai para o `localStorage` a cada tecla, porque no ginásio a app é fechada e reaberta muitas vezes.
    - Uma cópia local das sessões mais a reconciliação por `end` garantem que um treino gravado offline não se perde.
    - Só um treino em curso de cada vez, e só contam os exercícios visíveis e selecionados (os esbatidos ficam de fora).

---

## 6. Bugs e esquisitices atuais (não copiar)

1. **`getExDay(key)` deduz o dia a partir da key** (`key[1]`). Para `wC-0`, que está no Day A, devolve "C", e o esbatimento do Day A só se atualiza ao recarregar. Na aba nova, o dia vem do modelo e não da key.
2. **O histórico fica inflacionado.** Qualquer gravação (até ligar um checkbox) escreve `history[*][hoje]` para todos os exercícios com peso, mesmo sem treino nesse dia. Recomendação: a partir de agora, escreve `history` **só ao acabar um treino**, a partir das sessões, e mantém o histórico importado tal como está.
3. **Os custom não têm gráfico** em Progress (§2.4).
4. **O botão de apagar está escondido** e não há forma de restaurar um exercício apagado. Na aba nova: apagar com confirmação e, de preferência, um "restaurar".
5. **A seleção "doing today" nunca é limpa.** Considera limpá-la ao acabar o treino ou quando o dia muda. Confirma com o utilizador antes de mudar.
6. `applyWeights` só volta a calcular o esbatimento dos cards com linhas `.mob-r`. Os cards da Flexibility (`.mob-ex-full`) só ficam corretos porque `applySel`/`applyMobSel` correm também.
7. O `PATCH` envia o documento inteiro, por isso dois dispositivos a gravar ao mesmo tempo sobrescrevem-se (o último ganha). Se o backend novo permitir, faz merge por campo ou por sessão.
8. A UI mistura inglês e português de Portugal. Escolhe um idioma com o utilizador.
9. Valores com vírgula (`"27,5"`) existem nos dados reais. Usa sempre o `parseNum`.

---

## 7. Checklist de aceitação da aba nova

- [ ] As 7 sub-secções existem, com o conteúdo de §2 e §3.
- [ ] Day A–D colapsáveis, com exercícios na ordem gravada em `order` e os custom incluídos.
- [ ] Linha de exercício com seleção (esbate e sobe os selecionados), arrastar com toque no iOS, thumbnail com modal (`1.jpg`), campo kg com vírgula, stepper ±0,5 e ×1/×2.
- [ ] Painel de sets com pré-preenchimento, placeholder de reps da última sessão, +Set / −, volume por set e total, e badge no nome.
- [ ] O rascunho sobrevive a fechar a app. Só um treino em curso de cada vez. Acabar treino grava a sessão, atualiza o histórico (peso máximo do dia) e guarda a cópia local.
- [ ] Progress: Week/Month, máximo por período, duas séries com dois eixos, recordes no cabeçalho, estado vazio e gráficos também para os custom.
- [ ] Flexibility, Power e Achilles P4 com seleção e reordenação por card, thumbnail e link ▶.
- [ ] Adicionar exercício custom com nome obrigatório.
- [ ] Importa o `backups/gist-weights.json` atual sem perder chaves, e exporta no mesmo esquema.
- [ ] Indicador de sincronização e funcionamento offline (cache local mais envio quando houver rede).
- [ ] Nenhum dos bugs de §6 foi reproduzido.
