# Product–LiveChat Question Analysis

Product source: `json/ProductsDetailsExport.json`  
Chat source: `json/LiveChat all.json`  
Question extraction source: `json/livechat_customer_questions_chunks/`

## Executive summary

- Catalog records analyzed: **4,223**
- Unique catalog product IDs: **4,155** (68 duplicate-ID records in the export)
- LiveChat conversations scanned: **39,009**
- Extracted customer questions searched: **48,495**
- Catalog products connected to at least one question: **1,976**
- Products with at least one high-confidence connection: **1,282**
- Matched conversations: **4,546**
- Distinct matched customer questions: **9,380**
- Product-question associations: **13,833** (6,226 high confidence, 7,607 medium confidence)

The detailed, filterable result is in `json/product_livechat_questions.csv`. One customer question can be associated with more than one product when the conversation compares several product pages.

## Matching method

1. Direct product-page IDs from LiveChat URLs (`/p/{Id}`) were joined to the catalog `Id`.
2. Product codes from catalog names (the value after `|`) were matched exactly after punctuation/spacing normalization; refrigerant labels such as `R410A` were excluded.
3. Other customer questions from the same conversation were retained, which links follow-ups such as availability, price, compatibility, delivery, and returns to the identified product.
4. Appliance-model-only matches were intentionally excluded: one appliance model can map to many spare parts and would create substantial false positives.

High confidence means a unique exact code/customer-posted URL, or a conversation with one unambiguous visited/start product page. Shared codes and other URL-context matches are marked medium confidence.

## Match evidence

| Evidence | Associations |
|---|---:|
| customer_visited_product_url | 8,059 |
| start_page_url | 4,855 |
| agent_shared_product_url | 4,382 |
| customer_message_product_url | 1,155 |
| exact_product_code | 357 |
| unique_exact_product_code | 291 |

## Question themes

| Theme | Associations |
|---|---:|
| Product search / part identification | 5,750 |
| General question | 2,415 |
| Availability | 1,461 |
| Delivery / shipping | 1,442 |
| Compatibility / fit | 1,003 |
| Order / payment / invoice | 586 |
| Price | 407 |
| Store / contact | 316 |
| Dimensions / specs | 238 |
| Troubleshooting / usage | 149 |
| Returns / warranty | 66 |

## Categories with most question associations

| CategoryId | Associations | Distinct products |
|---:|---:|---:|
| 84 | 1,725 | 185 |
| 75 | 931 | 127 |
| 92 | 909 | 143 |
| 89 | 874 | 91 |
| 68 | 814 | 52 |
| 150 | 714 | 79 |
| 182 | 579 | 72 |
| 69 | 492 | 85 |
| 86 | 448 | 48 |
| 90 | 403 | 25 |
| 159 | 347 | 54 |
| 83 | 277 | 39 |
| 157 | 272 | 31 |
| 155 | 262 | 23 |
| 71 | 244 | 62 |
| 96 | 244 | 38 |
| 74 | 233 | 36 |
| 81 | 231 | 46 |
| 183 | 202 | 42 |
| 94 | 199 | 55 |

## Products with most customer questions

| ProductId | Questions | Chats | Product |
|---:|---:|---:|---|
| 505 | 142 | 49 | Помпа за пералня CANDY, GORENJE - ASKOLL 296005 \| 92129444 |
| 259 | 93 | 33 | Маншон за пералня ARISTON, INDESIT, HOTPOINT, WHIRLPOOL \| C00111416 |
| 237 | 92 | 45 | Преграда за барабан ARISTON, INDESIT, WHIRLPOOL \| 482000023096 |
| 3243 | 92 | 43 | Вакуум помпа едностъпална 1/5HP VALUE VH115N |
| 238 | 87 | 36 | Преграда за барабан ARISTON, INDESIT, HOTPOINT \| C00065463 |
| 3454 | 84 | 39 | Ключалка / дръжка за пералня GORENJE \| 333855 |
| 5256 | 81 | 36 | Маншон за пералня SAMSUNG \| DC64-02750A |
| 4112 | 77 | 29 | Вакуум помпа едностъпална 1/4HP VALUE VE115N |
| 224 | 75 | 30 | Амортисьор за пералня INDESIT - 100N, φ 13mm \| C00309597 |
| 289 | 73 | 32 | Маншон за пералня INDESIT, ARISTON, WHIRLPOOL \| C00103633 |
| 5002 | 68 | 31 | Маншон за пералня BEKO \| 2904520100 |
| 6830 | 66 | 21 | Манометричен блок, двоен R32, R134a, R404A, R410A в к-т с маркучи |
| 5915 | 64 | 27 | Ремък за пералня и сушилня 2010 H7 PH \| 480112101469 |
| 339 | 60 | 40 | Блокировка за пералня GORENJE - ZV 446 A2 \| 160966 |
| 779 | 58 | 28 | Ремък за пералня и сушилня 1975 H7 PH \| 481281728433 |
| 9888 | 54 | 25 | Текстилен плик / чувал за профилактика на климатици, 80cm / 140cm |
| 393 | 50 | 19 | Ключалка / дръжка за пералня INDESIT, ARISTON MERLONI \| C00075323 |
| 286 | 50 | 16 | Маншон за пералня INDESIT, ARISTON, WHIRLPOOL \| C00047099 |
| 4927 | 49 | 21 | Вакуум помпа eдностъпална 1/4HP VALUE V-i120SV с манометър |
| 399 | 48 | 22 | Ключалка / дръжка за пералня ARDO MERLONI, SAMSUNG \| 110284100 |
| 579 | 48 | 14 | Помпа за пералня VESTEL, CROWN, NEO - HANYU B12-6A01 \| M6532005187 |
| 11560 | 47 | 18 | Амортисьори за пералня WHIRLPOOL, INDESIT, ARISTON, HOTPOINT, 100N, φ8-13mm, комплект 2 броя + щифтове \| C00309597 |
| 5003 | 46 | 23 | Маншон за пералня GORENJE \| 581577 |
| 5135 | 45 | 26 | Амортисьор за пералня GORENJE - 120N, φ 8 - 12mm \| 111818 |
| 4687 | 45 | 20 | Маншон за пералня BALAY, BOSCH, SIEMENS \| 00361127 |
| 7939 | 45 | 19 | Помпа за пералня LG \| 5859EN1004B |
| 449 | 45 | 16 | Филтър за помпа за пералня GORENJE \| 279538 |
| 319 | 44 | 20 | Амортисьор за пералня GORENJE - 80-120N \| 634801 |
| 3686 | 43 | 18 | Ключалка / дръжка за пералня ARISTON MERLONI, INDESIT \| C00288568 |
| 3964 | 42 | 19 | Нагревател за пералня ZANUSSI, ELECTROLUX 1950W \| 1321020115 |
| 2843 | 42 | 18 | Оксижен 6 L |
| 3769 | 40 | 16 | Преграда за барабан ARISTON, INDESIT, WHIRLPOOL \| C00097565 |
| 2752 | 40 | 16 | Комплект накрайници с ръкохватка за горелка на оксижен (бренер) \| 690851 |
| 617 | 39 | 18 | Нагревател за пералня 2000W, единичен - ПЕРЛА |
| 5079 | 39 | 15 | Помпа за пералня, универсална - ASKOLL M114 292339 \| C00285437 |
| 9361 | 38 | 24 | Найлонов плик / чувал за профилактика на климатици ERRECOM WALLY |
| 614 | 38 | 20 | Нагревател за пералня 2050W, единичен - WHIRLPOOL IGNIS \| C00311143 |
| 465 | 38 | 16 | Помпа за пералня, универсална COPRECI, BEKO, SAMSUNG \| EBS2556-3404 |
| 888 | 38 | 12 | Лагер за пералня 6205 |
| 6446 | 37 | 18 | Маншон за пералня LG \| 4986ER1005A |

## Representative matched questions

### Помпа за пералня CANDY, GORENJE - ASKOLL 296005 \| 92129444 (`505`)

- `2026-05-18` `TF18Z4WNAZ` `Compatibility / fit` (`high`) — https://apogee99.com/pompa-za-peralnya-candy-gorenje-askoll-296005-or-92129444/p/505 Тази дали ще стане?
- `2026-05-18` `TF18Z4WNAZ` `Order / payment / invoice` (`high`) — Добре, ще пусна поръчка, благодаря ви!
- `2026-05-18` `TF18Z4WNAZ` `Delivery / shipping` (`high`) — Здравейте! Изпратиха ли се съобщенията ми преди да се включите в разговора или да ги изпратя наново
- `2026-05-18` `TF18Z4WNAZ` `Product search / part identification` (`high`) — Здравейте! Трябва ми помпа за стара пералня машина Самсунг. Помпата е Hanyu B20-6
- `2026-04-28` `TE27L5JXGI` `Availability` (`high`) — В София. Има ли ваш магазин

### Маншон за пералня ARISTON, INDESIT, HOTPOINT, WHIRLPOOL \| C00111416 (`259`)

- `2026-05-08` `TE0PPRW29S` `Product search / part identification` (`medium`) — Здравейте търся уплътнение за пералня indesit iwe 71282
- `2026-05-04` `TE5IR0RQ26` `Product search / part identification` (`medium`) — Бихте ли ми казали кой маншон да си купя за моята пералня?
- `2025-01-13` `SQ21T1OZWG` `General question` (`medium`) — Да, благодаря ви. Ако днес поръчам, кога ще може да е при мен :)
- `2025-01-13` `SQ21T1OZWG` `Product search / part identification` (`medium`) — здравейте, имате ли уплътнител за пералня за модел Hotpoint Ariston AQD970D49
- `2024-08-15` `SIB9M0D60H` `Delivery / shipping` (`medium`) — Поръчах го….кога се очаква доставката?

### Преграда за барабан ARISTON, INDESIT, WHIRLPOOL \| 482000023096 (`237`)

- `2026-02-23` `TA2WIUUZZG` `Availability` (`high`) — Имате ли го наличност?
- `2026-02-23` `TA2WIUUZZG` `General question` (`high`) — Ок кога ще дойде ако го поръчам днес
- `2026-02-23` `TA2WIUUZZG` `Product search / part identification` (`high`) — Трябва ми ребро за пералня whirlpool 12 дупки
- `2025-10-28` `T42UK9P7A9` `General question` (`high`) — Как мога да си променя номера ?
- `2025-08-21` `T10CL0SMUF` `General question` (`high`) — Може ли само с 2 единият се счупи

### Вакуум помпа едностъпална 1/5HP VALUE VH115N (`3243`)

- `2025-11-11` `T59KE09WFZ` `Product search / part identification` (`high`) — Какво масло трябва за този модел
- `2025-11-03` `T555JCUUTN` `Order / payment / invoice` (`high`) — Благодаря, сега ще оформя поръчка
- `2025-11-03` `T555JCUUTN` `Product search / part identification` (`high`) — Здравейте, тази вакуум помпа има ли си масло в комплекта? https://apogee99.com/vakuum-pompa-ednostupalna-15hp-value-vh115n/p/3243
- `2025-07-30` `T007ZM2DNC` `Availability` (`medium`) — Здравейте, следния артикул наличен ли е за изпращане по куриер в рамките на днешния ден? https://apogee99.com/fiting-suedinitelen-za-medni-trubi-edna-chetvart-zhenska-rezba/p/18637
- `2025-02-03` `SR53MP6WK0` `Product search / part identification` (`medium`) — В параметрите и пише 0.2 mBar, а тя по-ниско от 20 mBar не може да постигне ? Производителят ли лъже в параметрите или просто има дефект помпата?

### Преграда за барабан ARISTON, INDESIT, HOTPOINT \| C00065463 (`238`)

- `2026-01-27` `T91J32DL2F` `Price` (`high`) — А цената може ли
- `2026-01-27` `T91J32DL2F` `Troubleshooting / usage` (`high`) — Ще проверя и как да поръчам ако са същите
- `2025-12-05` `T60SNQMEQR` `Delivery / shipping` (`high`) — Днес ще мога ли да ги получа или...
- `2025-12-05` `T60SNQMEQR` `Delivery / shipping` (`high`) — Миналата седмица направих поръчка, но все още не ми е доставено
- `2025-12-05` `T60SNQMEQR` `General question` (`high`) — Мога ли да разбера защо?

### Ключалка / дръжка за пералня GORENJE \| 333855 (`3454`)

- `2025-12-16` `T75CVSP06Q` `Compatibility / fit` (`high`) — Дали е удобно да проверите за да знам дали да поръчам
- `2025-11-03` `T555F2YA9Y` `Compatibility / fit` (`high`) — Такава дръжка дали имате
- `2025-11-03` `T555F2YA9Y` `Availability` (`high`) — има ли инокс
- `2024-10-25` `SL0WWR8LN0` `Product search / part identification` (`high`) — Здравейте, търся дръжка-ключалка за пералня Горение - модел W9825I - при Вас има , но в бял цвят. Имате ли в сребърен металик?
- `2024-10-25` `SL0WWR8LN0` `Product search / part identification` (`high`) — Пералня Горение модел W9825I, art No 356676/03

### Маншон за пералня SAMSUNG \| DC64-02750A (`5256`)

- `2026-05-26` `TF5MXTN2G3` `Product search / part identification` (`high`) — Здравейте този маншон става ли за пералня с номер: WF60F4E0N0W/LE
- `2026-05-26` `TF5MXTN2G3` `Delivery / shipping` (`high`) — до офис на Еконт възможно ли е
- `2026-04-08` `TD36NJ6IQS` `Product search / part identification` (`medium`) — Ето по ясна снимка
- `2026-04-08` `TD36NJ6IQS` `General question` (`medium`) — Може ли да ми го пуснете за утре да е при мен
- `2026-03-24` `TC8EMLRH28` `General question` (`medium`) — Ако имате може ли да поръчам

### Вакуум помпа едностъпална 1/4HP VALUE VE115N (`4112`)

- `2025-12-02` `T69N1177Z9` `Product search / part identification` (`high`) — В смисъл дали държи налягане след спиране на помпата
- `2025-12-02` `T69N1177Z9` `Availability` (`high`) — Има ли клапан за обратно налягане
- `2025-12-02` `T69N1177Z9` `Product search / part identification` (`high`) — Питам за вакум помпата на valo тази ат 170лв.дали има клапан за обратно налягане
- `2025-11-03` `T555JCUUTN` `Order / payment / invoice` (`medium`) — Благодаря, сега ще оформя поръчка
- `2025-11-03` `T555JCUUTN` `Product search / part identification` (`medium`) — Здравейте, тази вакуум помпа има ли си масло в комплекта? https://apogee99.com/vakuum-pompa-ednostupalna-15hp-value-vh115n/p/3243

### Амортисьор за пералня INDESIT - 100N, φ 13mm \| C00309597 (`224`)

- `2025-11-04` `T5675CZ6KZ` `General question` (`medium`) — https://apogee99.com/amortisori-za-peralnya-whirlpool-indesit-ariston-hotpoint-c00309597/p/11560?utm_medium=chat&utm_campaign=link-shared-in-chat&utm_source=livechat.com&utm_content=apogee99.com
- `2025-11-04` `T5675CZ6KZ` `Delivery / shipping` (`medium`) — Готово направих поръчката. Ще може ли да ги изпратите днес?
- `2025-11-04` `T5675CZ6KZ` `General question` (`medium`) — Може ли тук да поръчам или през сайта?
- `2025-11-04` `T5675CZ6KZ` `Compatibility / fit` (`medium`) — С номера не става ли
- `2025-11-04` `T5675CZ6KZ` `Price` (`medium`) — Това цена за 2та ли е

### Маншон за пералня INDESIT, ARISTON, WHIRLPOOL \| C00103633 (`289`)

- `2026-02-16` `TA8J8JH1VZ` `Product search / part identification` (`high`) — търся маншон за пералня INDESITWG421TX
- `2023-01-30` `RPSAGO3PPK` `Product search / part identification` (`high`) — Нестава да ви пратя снимка незнам защо
- `2022-10-14` `RJFQNJUEOL` `Product search / part identification` (`medium`) — Необходим ми е за пералня модел Indesit WI40
- `2022-10-14` `RJFQNJUEOL` `Dimensions / specs` (`medium`) — ако е същия размер би трябвало да стане
- `2022-10-14` `RJFQNJUEOL` `Product search / part identification` (`medium`) — да изпратя снимка на панела

### Маншон за пералня BEKO \| 2904520100 (`5002`)

- `2026-03-12` `TB1SEBOB9C` `Product search / part identification` (`high`) — Въпроса ми как да сме сигурни че ще стане на моя модел
- `2026-03-12` `TB1SEBOB9C` `Delivery / shipping` (`high`) — Еконт село Градина област Пловдив
- `2026-03-12` `TB1SEBOB9C` `Store / contact` (`high`) — Или магазин в пловдив
- `2026-03-12` `TB1SEBOB9C` `Delivery / shipping` (`high`) — Кога може да го изпратите
- `2026-03-12` `TB1SEBOB9C` `Delivery / shipping` (`high`) — Спиди еконт

### Манометричен блок, двоен R32, R134a, R404A, R410A в к-т с маркучи (`6830`)

- `2025-09-29` `T32CBH77SJ` `General question` (`medium`) — /?удобно ли е сега да им звънна
- `2025-09-29` `T32CBH77SJ` `Product search / part identification` (`medium`) — може ли да питам нещо относно модел на вакум помпа
- `2025-04-14` `SU3P89KP8G` `Product search / part identification` (`medium`) — може ли да ми препоръчате вакуметър и маркуч.Бюджета ми е 200 лв като в тях трябва да влезе вакум помпа.Искам да дегазирам силикон или епоксидна смола в количества до половин килограм.
- `2024-08-28` `SIB8BRIX84` `Product search / part identification` (`medium`) — Добър ден. Мисля да закупя от вас вакуум помпа и манометри. Въпроса ми е , всички стоки ли имат две години гаранция?
- `2023-11-17` `S489NQFHU6` `Order / payment / invoice` (`medium`) — Добре откажете тази поръчка

### Ремък за пералня и сушилня 2010 H7 PH \| 480112101469 (`5915`)

- `2026-02-26` `T24OSOQBD9` `Product search / part identification` (`medium`) — ремък търся
- `2025-12-11` `T733SUO8O0` `Product search / part identification` (`high`) — Здравейте Ремък за пералня и сушилня 2010 H7 PH | 480112101469 дали е съвместим със сушилня WHIRLPOOL HDLH 70310
- `2025-12-11` `T733SUO8O0` `Product search / part identification` (`high`) — затова предполагам, че това което трябва да търся е 7PH 2010
- `2025-12-11` `T733SUO8O0` `General question` (`high`) — кога ще е при мен?
- `2025-12-11` `T733SUO8O0` `Order / payment / invoice` (`high`) — мога ли направо при вас да направя поръчка до адрес

### Блокировка за пералня GORENJE - ZV 446 A2 \| 160966 (`339`)

- `2026-05-04` `QG6CFEQYUZ` `Compatibility / fit` (`high`) — а дали имате и другото което е по дълго
- `2026-05-04` `QG6CFEQYUZ` `Compatibility / fit` (`high`) — здравейте!Дали имате уплатненията за съдомиална AEG F 55522WO
- `2026-05-04` `QG6CFEQYUZ` `Product search / part identification` (`high`) — извинете но дали имате и маншон заперална бекоWTE7636XA SAMO QE ZA NE[N[MAM DRUGI DANNI
- `2026-04-24` `QG6CFEQYUZ` `Product search / part identification` (`high`) — Уплътнение за хладилник SNAIGE RF270/RF315 - на жлеб, фризерна част | 100000 Здравейте! Имате ли го наличен?
- `2026-03-17` `QG6CFEQYUZ` `Product search / part identification` (`high`) — здравУплътнение за хладилник ELECTROLUX, AEG, ZANUSSI - на жлеб, фризерна част | 2248016590еите дали имате наличен 224801

### Ремък за пералня и сушилня 1975 H7 PH \| 481281728433 (`779`)

- `2026-05-27` `TE2VBFC9IB` `Availability` (`high`) — Има ли инструкция на бг
- `2025-03-04` `SS3LDI31UP` `Product search / part identification` (`high`) — Здравейте, търся ремък за сушилня PRIVILEG 6120CD. Не се чете добре написаното върху стария. Моля за съдействие.
- `2025-02-18` `SR3V3PW7PA` `Delivery / shipping` (`medium`) — Гр. Червен бряг офис еконт само 1 е града Маргарита Александрова
- `2025-02-18` `SR3V3PW7PA` `Price` (`medium`) — Да го поръчам и цена
- `2025-02-18` `SR3V3PW7PA` `Store / contact` (`medium`) — Да пусна адрес
