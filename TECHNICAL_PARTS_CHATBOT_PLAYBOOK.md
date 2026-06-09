# Technical Spare Parts Chatbot Playbook

This document explains how to use the 6-year LiveChat export to improve the CartAssist chatbot for a technical spare-parts ecommerce client.

Source analyzed:

```text
/home/xprmnt/dn-html-demo/json/LiveChat all.json
```

Generated aggregate summary:

```text
/home/xprmnt/dn-html-demo/json/livechat-analysis-summary.json
```

## 1. Executive Summary

The client does not need a generic ecommerce chatbot. The data shows they need a **technical compatibility support assistant**.

Customers usually do not ask only for a product by name. They ask whether a part fits a specific appliance, whether the shop has a replacement, what measurements are needed, whether an item is available, and how to order it.

The bot should operate as first-line customer support by doing four things consistently:

1. Identify the appliance and part family.
2. Collect required technical data: brand, model, serial/product number, dimensions, old part code, photos.
3. Search the product and compatibility database using exact model/part data first.
4. Give a safe answer, product recommendation, or escalate to a human when confidence is low.

The bot must be stricter than a normal sales assistant. It should avoid saying a part is compatible unless the catalog or compatibility data supports it.

## 2. Dataset Summary

The raw LiveChat export contains:

| Metric | Count |
|---|---:|
| Chats | 39,009 |
| Customer messages | 171,033 |
| Agent messages | 258,955 |
| Total message events | 429,988 |
| Chats with uploaded files/photos | 5,741 |
| Uploaded files/photos | 10,893 |
| Visited page records | 110,911 |
| Chats without agent messages | 5,345 |
| Median first agent response | 34.3 seconds |
| 75th percentile response | 71.5 seconds |
| 90th percentile response | 138.4 seconds |

This is enough data to build:

- intent taxonomy
- support playbook
- synonym dictionaries
- compatibility workflows
- follow-up question rules
- evaluation test set
- escalation policy

It should not be used raw in prompts or public frontend code because it may contain private customer information.

## 3. Core Business Reality

The primary support problem is **fitment uncertainty**.

Typical customer messages:

```text
Дали става за Snaige FR276?
```

```text
Търся маншон за тази пералня.
```

```text
Имам модел W84TXEX, какви части има?
```

```text
Пращам снимка, ако ще помогне.
```

Typical agent replies:

```text
На стикера трябва да има марка, модел, сериен и продуктов номер.
```

```text
Трябва да изпратите данните, за да проверим.
```

```text
Не мога да проверя и предложа част без данните.
```

This should become the bot’s default behavior.

## 4. Main Customer Intents

The bot should detect and handle all intents below.

### 4.1 Order And Delivery

Detected in about `28.0%` of chats.

Customer examples:

```text
Как да направя поръчка?
```

```text
Може ли да пратите по Еконт?
```

```text
Дайте ми банкова сметка за плащане по поръчка.
```

Bot should answer:

- how to order
- delivery options
- courier options: Speedy, Econt if supported
- payment methods
- what details are needed to place an order
- order status only if order lookup exists

Required slots:

```text
name
phone
delivery address or office
product id/name
quantity
payment method
```

Escalate when:

- customer asks about an existing paid order
- payment/bank transfer dispute
- delivery delay complaint
- invoice/company data issue

### 4.2 Availability / Stock Check

Detected in about `21.6%` of chats.

Customer examples:

```text
Имате ли налична тази част?
```

```text
Наличен ли е нагревателят?
```

Bot should answer:

- whether product is available if stock is known
- if no stock data exists, say availability must be confirmed
- show matching products
- ask for model/part data if the product is ambiguous

Required slots:

```text
product name or product id
part family
appliance model if compatibility is involved
```

Escalate when:

- stock data is missing and customer wants immediate confirmation
- item appears discontinued
- customer needs exact delivery date

### 4.3 Dimensions / Measurements

Detected in about `15.1%` of chats.

Customer examples:

```text
Нагревателят е 50 см на фи14.
```

```text
Какъв размер уплътнение ми трябва?
```

```text
Трябва ми ремък с тези размери.
```

Bot should extract:

```text
length_mm
width_mm
height_mm
diameter_mm
power_watt
voltage
mounting_type
shape
```

Bot should answer:

- if dimensions match a product, show products
- if dimensions are missing, ask for exact measurements
- for gaskets/seals, ask where it mounts and whether it is groove/magnetic/etc.
- for heaters, ask power, length, diameter, mounting/flange, connector type

Escalate when:

- dimensions conflict
- product is electrical/safety-sensitive and compatibility is unclear
- user asks to modify/adapt a part

### 4.4 Compatibility / Fitment Check

Detected in about `11.4%` of chats, but this is strategically the most important intent.

Customer examples:

```text
Става ли за Snaige FR276?
```

```text
Съвместим ли е с Delonghi Dinamica 350.50?
```

```text
Имам Whirlpool WA1010, какви части има?
```

Bot should use compatibility data first:

```text
Appliances.Brand
Appliances.Code
Appliances.SerialNumber
product compatibility rows
product title
product description
```

Required slots:

```text
appliance_type
brand
model
serial_number or product_number when available
part_family
```

If model/serial is missing, the bot should not guess. It should ask:

```text
За да проверя съвместимост, изпратете марка, модел и сериен/продуктов номер от стикера на уреда. Ако можете, изпратете снимка на стикера.
```

Escalate when:

- no exact compatibility match exists
- customer only has photo and no model data
- customer says the sticker is unreadable
- there are multiple possible versions for same model

### 4.5 Price Question

Detected in about `8.0%` of chats.

Customer examples:

```text
Каква е цената?
```

```text
Колко струва?
```

Bot should answer:

- product price if available
- if price missing in synced catalog, do not show `0.00`; say price must be confirmed or hide price
- show product card if product is identified

Required slots:

```text
product_id or product_name
```

Implementation note:

The current `ProductsDetailsExport.json` has no real price field. The sync currently sets price to `0.0`. For production this should be fixed by syncing prices from the ecommerce platform or suppressing price display for this store.

### 4.6 Identify Unknown Part

Detected in about `5.5%` of chats.

Customer examples:

```text
Може ли да ви пратя снимка?
```

```text
Търся тази част.
```

```text
Каква е тази част?
```

Bot should ask:

```text
Снимката полезна ли е като стара част или като стикер на уреда?
```

Then:

- if sticker photo: extract/ask brand, model, serial/product number
- if old part photo: ask appliance model and dimensions
- if part has code printed on it: ask for close-up of the code

Escalate when:

- image cannot be interpreted
- part is visually similar to multiple products
- customer needs guaranteed compatibility

### 4.7 Missing Model / Sticker Data

Detected explicitly in about `1.7%` of chats, but the real impact is larger because many compatibility chats depend on sticker data.

Customer examples:

```text
Надписът не е ясен.
```

```text
Няма стикер.
```

```text
Не знам модела.
```

Bot should guide by appliance type.

Sticker location guidance:

| Appliance | Where to look |
|---|---|
| Washing machine | Around door frame, back panel, filter area, inside service sticker |
| Fridge/freezer | Inside wall, side wall, near vegetable drawer, back label |
| Oven/cooker | Door frame, side of door, back plate |
| Dishwasher | Door edge, inner side of door |
| Dryer | Door frame, back label |
| Vacuum cleaner | Underside label, body sticker |
| Coffee machine | Bottom label, back label |
| Air conditioner | Indoor unit side label, outdoor unit plate |

If no sticker exists, bot should ask for:

```text
photos of the appliance
photos of old part
part dimensions
any numbers printed on old part
```

Then it should escalate if still uncertain.

### 4.8 Warranty / Return / Complaint

Detected in about `1.2%` of chats.

Bot should answer basic policy only if policy is known.

Escalate immediately for:

```text
warranty claim
return request
wrong item received
damaged delivery
refund
invoice issue
payment issue
```

## 5. Product Family Playbooks

### 5.1 Gaskets / Seals

Top family: `3,050` chats.

Common appliances:

```text
fridge/freezer
washing machine
oven/cooker
```

Required data:

```text
appliance brand
model
serial/product number
seal dimensions
mounting type: groove, magnetic, glued, door boot, etc.
photo of old seal
```

Bot behavior:

1. Ask appliance type.
2. Ask for model and serial/product number.
3. If fridge gasket: ask if it is fridge section or freezer section.
4. If dimensions are needed: ask width/height and mounting type.
5. Only show products with exact model or strong category/dimension match.

Example bot follow-up:

```text
За уплътнение трябва да проверим точния модел. Изпратете марка, модел и сериен/продуктов номер от стикера. Ако е хладилник, уточнете дали е за хладилна или фризерна част.
```

### 5.2 Heaters

Top family: `2,856` chats.

Common appliances:

```text
ovens/cookers
washing machines
water heaters
princess grills
```

Required data:

```text
appliance type
brand/model
power W
voltage
length
diameter
mounting/flange
connector type
shape
photo
```

Bot behavior:

1. Extract dimensions and wattage.
2. Ask for missing wattage/mounting/shape.
3. Warn that electrical parts need exact match.
4. Show products only if dimensions and mounting are compatible.

### 5.3 Pumps

Required data:

```text
appliance type
brand/model
pump type: drain/circulation
connector type
mounting type
old pump code
photo
```

Bot behavior:

- For washing machines, distinguish drain pump vs pump filter.
- Ask for old pump code if model search is unclear.

### 5.4 Belts

Required data:

```text
belt code printed on old belt
appliance type
brand/model
belt length/profile if code missing
```

Bot behavior:

- Prefer exact belt code.
- If no code, ask for model and measurements.

### 5.5 Door Handles / Locks

Required data:

```text
appliance brand/model
left/right orientation if relevant
photo of broken part
old part code if visible
```

Bot behavior:

- Ask for photos because similar handles can differ by small mounting points.

### 5.6 Filters

Required data:

```text
appliance type
brand/model
filter type: pump, water, vacuum, grease, HEPA
dimensions or old code
```

Bot behavior:

- Identify filter family before searching.

### 5.7 Boards / Programmers / Modules

Required data:

```text
appliance brand/model
module/programmer code
photo of label on module
symptom
```

Bot behavior:

- Never guarantee compatibility only from appliance model.
- Ask for module code.
- Escalate if code missing.

## 6. Appliance-Specific Flows

### 6.1 Washing Machines

Top appliance: `4,274` chats.

Common parts:

```text
seal/door boot
pump/filter
heater
belt
bearing
door lock
handle
motor brushes
```

Required slots:

```text
brand
model
serial/product number
part family
old part code or dimensions
photo when available
```

Bot first follow-up if data missing:

```text
За пералнята ми трябват марка, модел и сериен/продуктов номер от стикера. Обикновено е около люка или на задния панел. Можете да изпратите и снимка.
```

### 6.2 Fridges / Freezers

Top appliance: `3,791` chats.

Common parts:

```text
gaskets/seals
thermostats
sensors
doors/hinges
shelves/drawers
fans
compressor-related parts
```

Required slots:

```text
brand
model
serial/product number
fridge or freezer section
dimensions for gasket/shelf/drawer
photo
```

Bot first follow-up:

```text
За хладилник/фризер проверете стикера вътре в уреда, често на страничната стена или до чекмеджетата. Изпратете марка, модел и сериен/продуктов номер.
```

### 6.3 Ovens / Cookers

Top appliance: `3,677` chats.

Common parts:

```text
heaters
fan covers
fans
knobs
switches
thermostats
glass
gaskets
```

Required slots:

```text
brand
model
serial/product number
part family
heater dimensions/power if heater
photo
```

Bot first follow-up:

```text
При фурни и печки стикерът често е отстрани на вратичката, по рамката или на гърба. Изпратете марка, модел и сериен/продуктов номер, за да проверя.
```

### 6.4 Water Heaters

Common parts:

```text
heaters
anode protection
thermostats
flanges
gaskets
```

Required slots:

```text
brand
model
volume liters
heater type: dry/wet
power
flange type
photo
```

### 6.5 Air Conditioners

Common parts:

```text
remotes
sensors
fans
motors
filters
```

Required slots:

```text
brand
indoor unit model
outdoor unit model if relevant
remote model/code
photo
```

### 6.6 Dishwashers

Common parts:

```text
pumps
filters
heaters
spray arms
baskets
door seals
```

Required slots:

```text
brand
model
serial/product number
part family
old part code/photo
```

## 7. Bot Intent Taxonomy

Every customer message should be classified into one or more of these intents:

```text
greeting
product_search
compatibility_check
part_identification
availability_check
price_question
dimension_match
order_delivery
order_status
payment_invoice
warranty_return
technical_advice
photo_uploaded
model_data_missing
human_handoff_request
off_topic
```

Each intent should have:

```text
required_slots
optional_slots
search_strategy
safe_response_template
handoff_condition
```

## 8. Required Slot Model

The bot memory should store these fields:

```json
{
  "appliance_type": "washing_machine|fridge_freezer|oven_cooker|dishwasher|vacuum|dryer|coffee_machine|air_conditioner|water_heater|unknown",
  "brand": "",
  "model": "",
  "serial_number": "",
  "product_number": "",
  "part_family": "gasket|heater|pump|filter|belt|motor|sensor|board|handle|hose|bearing|unknown",
  "old_part_code": "",
  "dimensions": {
    "length_mm": null,
    "width_mm": null,
    "height_mm": null,
    "diameter_mm": null,
    "power_w": null,
    "voltage_v": null
  },
  "mounting_type": "",
  "uploaded_photo_type": "sticker|old_part|appliance|unknown",
  "current_product_id": "",
  "current_category_id": "",
  "confidence": 0.0
}
```

## 9. Search Strategy

Search should not be one generic vector query. Use a staged strategy.

### Stage 1: Exact Compatibility Search

If the user provides brand/model/serial:

```text
search compatibility collection first
match Appliances.Code
match Appliances.Brand
match Appliances.SerialNumber
```

Return exact compatible products first.

### Stage 2: Product Code / SKU Search

If user provides part code or article number:

```text
search sku/ean/model/product_id/search_terms
```

### Stage 3: Product Family + Appliance Search

If no exact model exists:

```text
part_family + appliance_type + brand + dimensions
```

### Stage 4: Semantic Catalog Search

Use vector search for vague descriptions only after exact fields are exhausted.

### Stage 5: Ask Follow-Up Or Handoff

If confidence is low:

```text
ask for sticker data, dimensions, old part code, or photo
```

If still low after one follow-up:

```text
handoff to human
```

## 10. Follow-Up Question Rules

### Compatibility query without model

```text
За да проверя съвместимост, изпратете марка, модел и сериен/продуктов номер от стикера на уреда. Можете да изпратите и снимка на стикера.
```

### Product family known, appliance unknown

```text
За какъв уред е частта: пералня, хладилник, фурна, съдомиялна или друг?
```

### Appliance known, part family unknown

```text
Каква част търсите за този уред: уплътнение, нагревател, помпа, филтър, ремък, брава, мотор или друго?
```

### Heater without dimensions

```text
За нагревател ми трябват мощност, дължина, диаметър/форма, захващане и снимка на старата част, ако е възможно.
```

### Gasket without dimensions/section

```text
За уплътнение уточнете дали е за хладилна или фризерна част и изпратете размери или модел от стикера.
```

### Customer has photo

```text
Снимката на стикера ли е или на старата част? Ако е на частта, моля изпратете и модел на уреда.
```

## 11. Safe Answer Rules

The bot should say:

```text
Намерих точен съвместим продукт според модела в каталога.
```

only when there is exact compatibility evidence.

The bot should say:

```text
Това изглежда като възможен вариант, но трябва да потвърдим по модел/сериен номер.
```

when search is semantic or dimension-only.

The bot should never say:

```text
Става 100%.
```

unless compatibility data explicitly confirms it.

## 12. Human Handoff Rules

Escalate immediately when:

```text
customer asks for human
warranty/return/refund/payment issue
order already placed and customer asks status
customer has unreadable sticker
multiple product variants fit the query
electrical/safety part with uncertain match
bot confidence below threshold after one follow-up
customer uploaded photo and image understanding is unavailable
```

Suggested handoff message:

```text
За да не ви подведа с грешна част, ще предам разговора на специалист. Моля оставете телефон или имейл и, ако можете, снимка на стикера/старата част.
```

## 13. Quick Replies For This Store

Replace perfume/service quick replies with technical parts quick replies:

```text
Търся част по модел уред
Провери съвместимост
Имам снимка на старата част
Провери наличност
Какви данни са нужни?
Поръчка и доставка
```

## 14. Welcome Message

Recommended welcome:

```text
Здравейте! Мога да помогна с резервни части по модел на уред, съвместимост, размери и наличност. Напишете марка и модел или изпратете снимка на стикера с данни.
```

## 15. Dashboard Configuration

For this client/store:

```text
Business model: ecommerce
Catalog profile: technical spare parts
Fragella/perfume: disabled
Service Assistant actions: disabled or replaced with technical quick replies
Product display: carousel
Max carousel products: 6
Human handoff: enabled
```

Branding:

```text
Agent name: Technical Parts Assistant
Primary color: #14120f
Secondary color: #c86b39
```

## 16. Product Sync Improvements

The current product export has fields:

```text
Id
Name
Description
Appliances
CategoryId
```

Recommended mapping:

```text
Id -> external_id/product_id
Name -> name
Description -> description/search text
Appliances[].Brand -> compatibility brand
Appliances[].Code -> compatibility model/code
Appliances[].SerialNumber -> compatibility serial/product number
CategoryId -> category id
```

Needed improvements:

1. Add real prices from ecommerce platform.
2. Add real stock/quantity.
3. Add product images.
4. Add product URLs.
5. Map category ids to human category names.
6. Extract product family from title/description.
7. Extract dimensions, wattage, voltage, diameter, mounting type.
8. Preserve compatibility rows but cap or batch them safely for sync.

## 17. Use The LiveChat Logs Safely

Do not use raw logs directly in prompts or frontend.

Reasons:

```text
IP addresses
names
phone numbers
emails
addresses
order numbers
private complaints
uploaded file URLs
```

Use logs only after anonymization and aggregation.

Safe derived artifacts:

```text
intent taxonomy
FAQ answers
slot extraction examples
support playbook
handoff rules
synonym lists
evaluation test set
```

## 18. Build An Evaluation Set

Create a file like:

```text
data/eval/technical_parts_eval.jsonl
```

Each row:

```json
{
  "query": "Търся маншон за пералня Beko WTE 7612 BS",
  "intent": "compatibility_check",
  "appliance_type": "washing_machine",
  "part_family": "gasket_seal",
  "brand": "BEKO",
  "model": "WTE 7612 BS",
  "expected_behavior": "search compatibility first; show exact products or ask for serial/product number",
  "must_not_do": "do not claim compatibility without evidence"
}
```

Recommended evaluation size:

```text
Phase 1: 100 examples
Phase 2: 500 examples
Phase 3: 1,000 examples
```

Categories should cover:

```text
compatibility
availability
dimensions
unknown part/photo
order/delivery
price
warranty/return
missing model data
```

## 19. Training / Prompt Assets To Extract

From the logs, create these assets:

### 19.1 Intent Examples

For each intent, collect 50-200 anonymized user messages.

### 19.2 Follow-Up Templates

Extract agent phrasing and rewrite as clean bot templates.

### 19.3 Synonym Dictionary

Examples:

```text
уплътнение, гума, гарнитура -> gasket_seal
нагревател, реотан, спирала -> heater
помпа, помпичка -> pump
брава, заключалка -> door_lock
ремък, ремак -> belt
```

### 19.4 Appliance Dictionary

Examples:

```text
пералня, washer -> washing_machine
хладилник, фризер, fridge, freezer -> fridge_freezer
печка, фурна, котлон, oven, cooker, hob -> oven_cooker
съдомиялна -> dishwasher
прахосмукачка -> vacuum
```

### 19.5 Brand Dictionary

Common brands from logs:

```text
GORENJE
WHIRLPOOL
INDESIT
BEKO
AEG
SAMSUNG
BOSCH
ARISTON
ELECTROLUX
ZANUSSI
LG
CANDY
HOTPOINT
SIEMENS
SNAIGE
```

## 20. Implementation Roadmap

### Phase 1: Configuration Fixes

1. Disable perfume/Fragella for technical-parts store.
2. Replace quick replies.
3. Set technical spare-parts profile.
4. Hide prices if real prices are unavailable.
5. Confirm public widget key works.

### Phase 2: Retrieval Improvements

1. Improve product sync metadata.
2. Add category name mapping.
3. Add compatibility-first search.
4. Add exact model/code matching.
5. Add dimension extraction.
6. Add appliance/part family extraction.

### Phase 3: Conversation Logic

1. Add intent router for technical support.
2. Add required slot memory.
3. Add follow-up rules.
4. Add confidence thresholds.
5. Add handoff policy.

### Phase 4: Evaluation

1. Build 100-example eval set from logs.
2. Run eval before every change.
3. Track false compatibility claims separately.
4. Track unnecessary handoffs separately.
5. Track successful product recommendations.

### Phase 5: Advanced Features

1. Photo/sticker OCR.
2. Order-aware support.
3. Product-page-aware assistant.
4. Admin review queue for low-confidence chats.
5. Auto-summarized handoff notes for human agents.

## 21. Success Metrics

Track these metrics after deployment:

```text
percentage of chats resolved by bot
number of compatibility checks completed
number of product cards shown
conversion after bot recommendation
handoff rate
handoff quality
wrong-part complaint rate
average time to answer
missing-data follow-up completion rate
```

Critical quality metric:

```text
false compatibility claims = 0 target
```

For technical spare parts, avoiding a wrong recommendation is more important than maximizing product suggestions.

## 22. Recommended Bot Policy

The bot should act like a careful technical support agent:

```text
Ask for exact data before recommending.
Use compatibility data before semantic search.
Give product suggestions only when evidence is strong.
Explain what data is missing.
Escalate when uncertainty remains.
Never invent compatibility.
```

## 23. Immediate Next Actions

1. Fix dashboard store config: remove perfume/service quick replies.
2. Update widget welcome/quick replies for technical parts.
3. Hide `0.00` prices or sync real prices.
4. Build technical intent router.
5. Build 100-example evaluation set from the LiveChat logs.
6. Implement compatibility-first search using `Appliances` rows.
7. Add human handoff for low-confidence compatibility.


## 24. VPS Changes Made During This Session

This section records the production/VPS operational changes made for the `test.cartassist.shop` sample demo and dashboard integration.

Date of work: 2026-06-06

VPS public IP:

```text
144.91.84.91
```

Target demo domain:

```text
test.cartassist.shop
```

### 24.1 DNS Change Required / Added

A new DNS A record was required for the demo subdomain:

```text
Type: A
Name: test
Value: 144.91.84.91
TTL: 300
```

Verification command:

```bash
dig +short test.cartassist.shop
```

Expected result:

```text
144.91.84.91
```

### 24.2 Demo App Directory On VPS

The demo app was deployed under:

```text
/srv/apps/dn-html-demo
```

The large product database was copied separately because GitHub rejects normal Git blobs over 100 MB.

Large product DB path:

```text
/srv/apps/dn-html-demo/json/ProductsDetailsExport.json
```

The directory was created with:

```bash
ssh root@144.91.84.91 'mkdir -p /srv/apps/dn-html-demo/json'
```

The product DB was uploaded with `scp`, using the absolute/local path when needed:

```bash
scp /home/xprmnt/dn-html-demo/json/ProductsDetailsExport.json root@144.91.84.91:/srv/apps/dn-html-demo/json/ProductsDetailsExport.json
```

Because the file was initially uploaded as root with restrictive permissions, permissions were fixed:

```bash
chmod 755 /srv/apps/dn-html-demo/json
chmod 644 /srv/apps/dn-html-demo/json/ProductsDetailsExport.json
```

### 24.3 GitHub Large File Issue

The first `git push` failed because:

```text
json/ProductsDetailsExport.json is 145.62 MB; this exceeds GitHub's file size limit of 100.00 MB
```

Resolution:

```bash
git rm --cached json/ProductsDetailsExport.json
printf "\n# Large local product exports\njson/ProductsDetailsExport.json\n" >> .gitignore
git add .gitignore
git commit --amend --no-edit
git push
```

Later, these additional ignore rules were added to avoid committing raw/private chat exports and generated analysis:

```text
json/LiveChat all.json
json/livechat-analysis-summary.json
json/ProductsDetailsExport.json
```

### 24.4 Code Deployment On VPS Without Overwriting Large JSON

Because `/srv/apps/dn-html-demo` already contained the manually uploaded `json/` directory, the repo was cloned into a temporary directory and synced without overwriting `json/`:

```bash
su -- root
cd /srv/apps
rm -rf /srv/apps/dn-html-demo-tmp
git clone https://github.com/nikolaysaev/dn-ms-demo.git dn-html-demo-tmp
rsync -a --exclude json /srv/apps/dn-html-demo-tmp/ /srv/apps/dn-html-demo/
rm -rf /srv/apps/dn-html-demo-tmp
```

Verification commands:

```bash
ls -lah /srv/apps/dn-html-demo
ls -lah /srv/apps/dn-html-demo/deploy/systemd/dn-html-demo.service
ls -lah /srv/apps/dn-html-demo/deploy/nginx/test.cartassist.shop.conf
ls -lh /srv/apps/dn-html-demo/json/ProductsDetailsExport.json
```

### 24.5 Demo Systemd Service

A dedicated systemd service was added for the sample shop only. This avoids touching other apps.

Template committed in repo:

```text
deploy/systemd/dn-html-demo.service
```

Installed on VPS:

```bash
cp /srv/apps/dn-html-demo/deploy/systemd/dn-html-demo.service /etc/systemd/system/dn-html-demo.service
systemctl daemon-reload
systemctl enable --now dn-html-demo
systemctl status dn-html-demo --no-pager
```

Service behavior:

```text
Runs /srv/apps/dn-html-demo/main.py
Binds to 127.0.0.1:8090
Runs as devops according to template
```

Local service check:

```bash
curl -I http://127.0.0.1:8090/
```

Expected result:

```text
HTTP/1.0 200 OK
```

### 24.6 Missing Summary JSON On VPS

Because `rsync --exclude json` preserved the uploaded product DB but skipped the small Git-tracked summary file, this file was missing initially:

```text
/srv/apps/dn-html-demo/json/products-demo-summary.json
```

It caused:

```text
404 File not found
```

The summary was regenerated on the VPS from the full product DB:

```bash
cd /srv/apps/dn-html-demo

python3 - <<'PY'
import json, re
from pathlib import Path

src = Path('json/ProductsDetailsExport.json')
out = Path('json/products-demo-summary.json')

with src.open(encoding='utf-8') as f:
    data = json.load(f)

def clean(text, limit=180):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    return text[:limit].rstrip() + ('...' if len(text) > limit else '')

cats = {}
samples = []

for item in data:
    if not isinstance(item, dict):
        continue
    cat = item.get('CategoryId') or item.get('category') or item.get('category_id') or 'unknown'
    cats[str(cat)] = cats.get(str(cat), 0) + 1
    if len(samples) < 8:
        samples.append({
            'id': item.get('Id') or item.get('id') or item.get('product_id'),
            'name': clean(item.get('Name') or item.get('name') or item.get('title'), 140),
            'categoryId': item.get('CategoryId') or item.get('category_id'),
            'description': clean(item.get('Description') or item.get('description'), 220),
            'appliances': item.get('Appliances') or item.get('appliances') or [],
        })

summary = {
    'source': 'json/ProductsDetailsExport.json',
    'recordCount': len(data),
    'fileSizeBytes': src.stat().st_size,
    'schema': list(data[0].keys()) if data and isinstance(data[0], dict) else [],
    'categoryCount': len(cats),
    'topCategories': [
        {'categoryId': k, 'count': v}
        for k, v in sorted(cats.items(), key=lambda kv: kv[1], reverse=True)[:10]
    ],
    'samples': samples,
    'notes': [
        'This summary is for the demo page only.',
        'The full product database remains json/ProductsDetailsExport.json.',
        'The export uses capitalized keys: Id, Name, Description, Appliances, CategoryId.'
    ]
}

out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'wrote {out}')
PY

chmod 644 json/products-demo-summary.json
```

Verification:

```bash
curl -sS http://127.0.0.1:8090/json/products-demo-summary.json | head
```

Expected result includes:

```json
{
  "source": "json/ProductsDetailsExport.json",
  "recordCount": 4223,
  "fileSizeBytes": 152694267
}
```

### 24.7 Nginx Site For `test.cartassist.shop`

A dedicated nginx site was added. It proxies only `test.cartassist.shop` to the local demo service on port `8090`.

Template committed in repo:

```text
deploy/nginx/test.cartassist.shop.conf
```

Installed on VPS:

```bash
cp /srv/apps/dn-html-demo/deploy/nginx/test.cartassist.shop.conf /etc/nginx/sites-available/test.cartassist.shop.conf
ln -sf /etc/nginx/sites-available/test.cartassist.shop.conf /etc/nginx/sites-enabled/test.cartassist.shop.conf
nginx -t
systemctl reload nginx
```

HTTP check:

```bash
curl -I http://test.cartassist.shop/
```

### 24.8 HTTPS Certificate

HTTPS was added with Certbot after DNS resolved:

```bash
certbot --nginx -d test.cartassist.shop
```

Verification:

```bash
nginx -t
systemctl reload nginx
curl -I https://test.cartassist.shop/
certbot certificates | grep -A8 test.cartassist.shop
```

Observed successful result:

```text
HTTP/2 200
Certificate Name: test.cartassist.shop
Domains: test.cartassist.shop
Expiry Date: 2026-09-04
Certificate Path: /etc/letsencrypt/live/test.cartassist.shop/fullchain.pem
Private Key Path: /etc/letsencrypt/live/test.cartassist.shop/privkey.pem
```

Nginx produced an existing warning unrelated to this demo site:

```text
protocol options redefined for [::]:443 in /etc/nginx/sites-enabled/dn-website.conf:11
```

This was not blocking; nginx config test passed.

### 24.9 Recommended Nginx Security Improvement

Because bots requested paths like `/.env` and `/.git`, this location block was recommended for the `test.cartassist.shop` nginx server block:

```nginx
location ~ /\.(?!well-known) {
    deny all;
}
```

Then reload:

```bash
nginx -t
systemctl reload nginx
```

### 24.10 Dashboard Store Created

A production dashboard store was created manually through the dashboard UI for:

```text
Domain: test.cartassist.shop
Business model: ecommerce
Integration type: custom
```

The dashboard provided:

```text
Public key: fiT5lMJiXCoHUfRzvHduFA
Store id observed in sync responses: 4
```

Important distinction:

```text
Public key -> browser/widget only
Secret key -> server-side API calls only, such as product sync
```

The secret key must never be added to frontend code.

### 24.11 Widget Linking

The sample page was configured to use the production dashboard widget on `test.cartassist.shop`.

Frontend widget config:

```html
<script>
window.DN_CHATBOT_CONFIG = {
  storeId: "demo-store",
  apiKeyPublic: "fiT5lMJiXCoHUfRzvHduFA",
  apiUrl: "https://dashboard.cartassist.shop/v1",
  position: "bottom-right"
};
</script>
<script src="https://dashboard.cartassist.shop/v1/widget/dn-chatbot.min.js" async></script>
```

The sample page also auto-switches to production URLs when opened on `test.cartassist.shop`:

```text
Widget script URL: https://dashboard.cartassist.shop/v1/widget/dn-chatbot.min.js
Dashboard public API base: https://dashboard.cartassist.shop/v1
Core API base: https://api.cartassist.shop
```

### 24.12 Dashboard CORS Update

The dashboard initially did not include `https://test.cartassist.shop` in CORS origins.

Current env inspected:

```bash
cd /srv/apps/dn-chatbot-dashboard
grep -nE '^(CORS_ORIGINS|CHATBOT_API_URL|API_BASE_URL)=' .env || true
```

Observed before patch:

```text
API_BASE_URL=https://api.cartassist.shop
CORS_ORIGINS=https://dashboard.cartassist.shop,https://cartassist.shop,https://www.cartassist.shop,https://lexo.bg,https://www.lexo.bg
CHATBOT_API_URL=http://127.0.0.1:8001
```

Patch command used/recommended:

```bash
cd /srv/apps/dn-chatbot-dashboard

cp .env .env.backup.$(date +%Y%m%d-%H%M%S)

python3 - <<'PY'
from pathlib import Path

p = Path(".env")
lines = p.read_text().splitlines()
target = "https://test.cartassist.shop"
out = []

for line in lines:
    if line.startswith("CORS_ORIGINS="):
        key, value = line.split("=", 1)
        origins = [x.strip() for x in value.split(",") if x.strip()]
        if target not in origins:
            origins.insert(0, target)
        line = key + "=" + ",".join(origins)
    out.append(line)

p.write_text("\n".join(out) + "\n")
PY

grep -n '^CORS_ORIGINS=' .env
```

Restart dashboard:

```bash
systemctl restart dn-dashboard
systemctl status dn-dashboard --no-pager
```

CORS verification:

```bash
curl -i -X OPTIONS 'https://dashboard.cartassist.shop/v1/chat/ask' \
  -H 'Origin: https://test.cartassist.shop' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type' | head -40
```

Expected header:

```text
Access-Control-Allow-Origin: https://test.cartassist.shop
```

### 24.13 Product Sync Script Added On VPS

A script was created on the VPS to convert `ProductsDetailsExport.json` into the dashboard `/v1/sync` product payload shape:

```text
/srv/apps/dn-html-demo/sync_products.py
```

Purpose:

```text
Id -> external_id
Name -> name
Description -> description
CategoryId -> categories/attributes
Appliances -> compatibility rows
```

The script posts to:

```text
https://dashboard.cartassist.shop/v1/sync
```

Authentication:

```text
Authorization: Bearer <secret key>
```

The secret key was exported in the shell only:

```bash
export DN_DEMO_SECRET_KEY='...secret...'
```

It must not be committed or added to frontend code.

### 24.14 Product Sync Test And Full Sync

A tiny sync test succeeded:

```bash
python3 sync_products.py \
  --key "$DN_DEMO_SECRET_KEY" \
  --limit 3 \
  --batch-size 3
```

Observed result:

```json
{"synced": 3, "total": 3, "compatibility_synced": 0, "compatibility_collection": null, "message": "Successfully synced 3 products to Qdrant"}
```

A full sync with `--batch-size 100` failed due to nginx body size:

```text
413 Request Entity Too Large
```

A full sync with `--batch-size 10` initially failed on OpenAI embeddings because some descriptions were too long:

```text
400 Bad Request for https://api.openai.com/v1/embeddings
```

The script was patched to truncate text:

```text
name limit: 320 characters
description limit: 2500 characters
```

Then `--batch-size 10` later failed on another oversized payload due to very large `Appliances` arrays.

A compatibility cap was recommended/added:

```text
normalize_appliances(rows, limit=80)
```

Successful full sync result:

```text
Done. Synced 4223/4223 products.
```

The sync created product vectors and compatibility data in Qdrant. Store id observed in compatibility collection:

```text
store_4_compatibility
```

### 24.15 Chat API Verification

Public key chat session test:

```bash
curl -sS -X POST https://dashboard.cartassist.shop/v1/chat/session \
  -H "Content-Type: application/json" \
  -d '{
    "api_key_public": "fiT5lMJiXCoHUfRzvHduFA",
    "session_id": "debug_demo_1"
  }' | python3 -m json.tool
```

Observed:

```json
{
  "ok": true,
  "session_id": "debug_demo_1",
  "status": "ai",
  "product_count": 0,
  "fragella_enabled": false
}
```

Public key ask test:

```bash
curl -i -sS -X POST https://dashboard.cartassist.shop/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "api_key_public": "fiT5lMJiXCoHUfRzvHduFA",
    "session_id": "debug_demo_1",
    "user_text": "Покажи диамантена боркорона ROTHENBERGER"
  }' | head -120
```

Observed:

```text
HTTP/2 200
```

The response returned product cards, proving:

```text
public key works
dashboard can look up the store
dashboard can proxy to core
Qdrant product sync works
```

### 24.16 Production Services Touched

Service list observed:

```text
cars-plugin-app.service
 dn-chatbot.service
 dn-dashboard.service
 dn-html-demo.service
 dn-ms-demo.service
 dn-website-backend.service
 dn-website-frontend.service
```

Services restarted or started during the session:

```bash
systemctl enable --now dn-html-demo
systemctl restart dn-html-demo
systemctl restart dn-chatbot
systemctl restart dn-dashboard
systemctl reload nginx
```

Reason:

- `dn-html-demo`: new sample shop service
- `nginx`: new test domain config and SSL
- `dn-dashboard`: apply CORS/env changes
- `dn-chatbot`: recover/reload chatbot core after production services were found down/stale

### 24.17 Important Operational Notes

1. The sample storefront uses only the public key.
2. Product sync uses the secret key server-side only.
3. Raw product and LiveChat JSON files are too large/private for Git.
4. The current product sync sets prices to `0.0` because the export has no price field.
5. Price display should be hidden or real prices should be synced from the ecommerce system.
6. The dashboard store still showed some old perfume/service quick replies at one point; those should be removed for technical-parts behavior.
7. CORS must include `https://test.cartassist.shop` for browser widget calls.
8. The direct core test panel on the sample page is only for debugging; the real widget flow uses the public key through the dashboard.

### 24.18 Commands For Future Code Updates

Local machine:

```bash
cd /home/xprmnt/dn-html-demo
git status
git add index.html README.md DEPLOY_TEST.md deploy TECHNICAL_PARTS_CHATBOT_PLAYBOOK.md .gitignore
git commit -m "Update demo shop and technical parts playbook"
git push
```

VPS:

```bash
su -- root
cd /srv/apps/dn-html-demo
git pull
systemctl restart dn-html-demo
curl -I https://test.cartassist.shop/
```

Do not overwrite `/srv/apps/dn-html-demo/json/ProductsDetailsExport.json` unless intentionally updating the product database.

