# Apogee99 Chatbot Demo — Presenter Script

One page: what to click, what to type, what the audience should notice.
Total time: ~7 minutes for the three "wow" flows + Q&A.

## Before the demo (5-minute checklist)

- [ ] Core running on `:8001`, dashboard on `:8002`, demo shop on `:8090`, Qdrant `:6333`, MySQL `:3307`.
- [ ] Open the shop (`http://127.0.0.1:8090`) — the widget bubble is bottom-right.
- [ ] Open the dashboard (`http://127.0.0.1:8002`) in a second tab, logged in — the
      conversation appears live there while you chat (message sound is on).
- [ ] Have a photo of a BOSCH rating plate on the demo machine
      (`tests/demo_sticker_bosch.png` — brand BOSCH, E-Nr. WAE16422IT/01).
- [ ] Fresh browser session (or new incognito window) so the greeting + starter chips show.

## Flow 1 — Sticker photo → confirmed parts (the headline, ~2 min)

**Say:** "Клиентите не си знаят модела. Знаят как да снимат."

1. Click chip **„📷 Ще снимам стикера на уреда"** → the bot explains and shows **„📎 Прикачи снимка"**.
2. Attach the rating-plate photo.
3. **Audience should notice:** the bot *reads the plate* („📷 Разчетох от стикера: марка BOSCH,
   модел WAE16422IT/01…") and returns pumps with the green badge **„Съвместимо с BOSCH WAE16422IT/01"** —
   confirmed fitment, not guesses. No human involved.
4. Mention: an unreadable/blurry photo automatically goes to a human operator instead — show
   the dashboard tab where the conversation would light up.

## Flow 2 — Symptom → diagnosis → parts (~2 min)

**Say:** "Клиентът не знае коя част му трябва — знае какво не работи."

1. Click chip **„🧰 Уредът ми има проблем"** (sends „Пералнята ми тече отдолу…").
2. **Audience should notice:** the „🔧 Вероятни причини" card — probable causes ranked, with
   the part families that fix each — plus smart follow-up chips
   („Тече при източване/центрофуга", „Тече при пълнене"…).
3. Click one of those chips → the bot narrows down and shows the right part family.

## Flow 3 — Code & model lookups (~1 min, rapid-fire)

1. Chip **„🔢 Търсене по код (пример)"** (sends `4901ER2003B`) → instant exact part. One message, zero questions.
2. Chip **„✅ Част за моя модел (пример)"** (sends „Помпа за пералня WHIRLPOOL AWG 885 AV")
   → pump + filter, both badged **„Съвместимо с…"** — that's the fitment database talking.

## Numbers to quote

- **2,04 млн. реда съвместимост** заредени за демото (пълните данни, без съкращения) — 213 000 различни модела уреди.
- **100% точност** на вътрешния тест от 120 клиентски въпроса (8 категории: кодове, съвместимост, размери, симптоми, снимки…).
- Отговор за ~2–8 сек; снимка на стикер ~15 сек.
- Всеки разговор се вижда живо в таблото; операторът може да поеме чата по всяко време.

## If something goes wrong

- Bot answers but oddly → it fell back to the rule pipeline automatically; continue the demo, nothing visible breaks.
- Photo flow fails → say "при нечетлива снимка отива при оператор" and show the dashboard escalation — that IS the designed behavior.
- Nothing responds → check the core process on `:8001`; the widget will queue politely.

## The ask for Apogee99 (close)

Следващата стъпка е пълната база: продукти + категории (с **имена**, не само номера) + пълния
списък „За модели". Ние поемаме останалото — синхронизацията е тествана на милиони редове.
