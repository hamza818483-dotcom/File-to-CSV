import os, re, pandas as pd, email, requests, base64, time, io, sys, gc, asyncio, urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
from email import policy
from PIL import Image
from pyrogram import Client, filters
from pyrogram.enums import ParseMode

# --- ১. CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "33312774"))
API_HASH = os.environ.get("API_HASH", "883db3366f8759d1d14c861c0d628232")
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN", "8741087357:AAFu-cAdnYAqfvCvZbX7gIATJMMRR8bLOVA")

API_KEYS = [
    "a74dc88809cedadda845003a16bb4bc7",
    "baaf0490e7c82522b8f21367a16bb4bc7",
    "10b5bc5469e5bf8c9d7f3565e44e7380",
    "1bbde6aba5711a01ee39da3fc678ce41",
    "7de311738b50e4036a8486f03cc2d2ed",
    "30cb522cec07fee7457baca2794c091b",
    "19fa44c34118d9ca97677e2a382af738"
]
current_key_index = 0

# Serial Processing Queue
processing_queue = asyncio.Queue()
is_processing = False

# --- PROGRESS HELPER FUNCTION ---
async def progress(current, total, message, start_time):
    now = time.time()
    diff = now - start_time
    if diff < 1: return 
    
    speed = current / diff if diff > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0
    
    current_mb = current / (1024 * 1024)
    total_mb = total / (1024 * 1024)
    speed_mb = speed / (1024 * 1024)
    
    progress_str = (
        f"📥 **Downloading File**\n\n"
        f"📊 **Size:** `{current_mb:.2f} / {total_mb:.2f} MB`\n"
        f"🚀 **Speed:** `{speed_mb:.2f} MB/s`\n"
        f"⏳ **ETA:** `{int(eta//60):02d}:{int(eta%60):02d}`"
    )
    
    try:
        if int(diff) % 5 == 0:
            await message.edit_text(progress_str)
    except: pass

# --- ২. CORE UTILITIES ---
def convert_to_english_numbers(text):
    return text.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))

def compress_image(b64_str):
    try:
        img_data = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(img_data))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", optimize=True, quality=70)
        return base64.b64encode(out_buffer.getvalue()).decode('utf-8')
    except: return b64_str

def upload_to_imgbb(b64):
    global current_key_index
    if not b64: return ""
    compressed = compress_image(b64)
    for _ in range(len(API_KEYS)):
        try:
            res = requests.post("https://api.imgbb.com/1/upload", data={"key": API_KEYS[current_key_index], "image": compressed}, timeout=12)
            if res.status_code == 200: 
                return res.json()['data']['url']
            current_key_index = (current_key_index + 1) % len(API_KEYS)
        except:
            current_key_index = (current_key_index + 1) % len(API_KEYS)
    return ""

def aggressive_clean(text):
    if not text: return ""
    text = convert_to_english_numbers(text)
    
    text = re.sub(r'\\frac\s*\{([^}]+)\}\s*\{([^}]+)\}', r'\1/\2', text)
    text = re.sub(r'_\{\s*([^}]+)\s*\}', r'_\1', text) 
    text = re.sub(r'\^\{\s*([^}]+)\s*\}', r'^\1', text) 
    text = re.sub(r'_([0-9a-zA-Z+-]+)', lambda m: m.group(1).translate(str.maketrans("0123456789+-=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")), text)
    text = re.sub(r'\^([0-9a-zA-Z+-]+)', lambda m: m.group(1).translate(str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₌⁽⁾ⁿ")), text)
    
    sup_to_normal = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    text = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹]+)°', lambda m: m.group(1).translate(sup_to_normal) + '°', text)
    text = text.replace('^\\circ', '°').replace('^{\\circ}', '°').replace('∘', '°').replace('° C', '°C').replace('^ C', '°C')
    
    sub_chars = str.maketrans("ₐₑₒₓₕₖₗₘₙₚₛₜ", "aeoxhklmnpst")
    text = text.translate(sub_chars)
    
    text = re.sub(r'\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]+)', r'\1', text)
    text = text.replace('₍', '(').replace('₎', ')')
    text = re.sub(r'(?<=[A-Za-z])\s+(?=[a-z](?:\s|$|[^a-zA-Z]))', '', text)
    text = re.sub(r'(?<=\d)\s+(?=[A-Z])', '', text)                        
    text = re.sub(r'(?<=[A-Z])\s+(?=[A-Z])', '', text)                     
    text = re.sub(r'(?<=[A-Z])\s+(?=[a-z](?:\s|$|[^a-zA-Z]))', '', text)   
    text = re.sub(r'(?<=[A-Z][a-z])\s+(?=[A-Z])', '', text)                
    text = re.sub(r'(?<=[₀-₉⁰-⁹])\s+(?=[A-Z])', '', text)                  
    text = text.replace(' . ', '.').replace(' .', '.').replace('. ', '.')

    text = re.sub(r'\\[a-zA-Z]+\s*\{?', ' ', text)
    text = re.sub(r'([A-Z][a-z]?)\s+([₀-₉⁰-⁹⁺⁻])', r'\1\2', text)
    
    units = r'(mL|L|m³|cm³|g|kg|mol|M|Pa|atm|J|K|V|A|W|N|C|Hz|eV|nm|mm|cm|m)'
    text = re.sub(r'(\d+)\s*' + units + r'\b', r'\1 \2', text)
    text = re.sub(r'(\d+)(' + units + r')\b', r'\1 \2', text)
    text = re.sub(r'[\{\}]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_content(element, img_map):
    if not element: return ""
    
    for hidden in element.find_all(['annotation', 'script', 'mjx-assistive-mathml']):
        hidden.decompose()
    for hidden in element.find_all('span', class_=['katex-html', 'MJX_Assistive_MathML', 'MathJax_Preview']):
        hidden.decompose()
        
    for mfrac in element.find_all('mfrac'):
        contents = mfrac.find_all(recursive=False)
        if len(contents) == 2:
            num = contents[0].get_text(strip=True)
            den = contents[1].get_text(strip=True)
            mfrac.replace_with(f"{num}/{den}")
        
    sub_map = str.maketrans("0123456789+-=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")
    sup_map = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₌⁽⁾ⁿ")
    
    for sub in element.find_all(['sub', 'msub']): 
        sub.replace_with(sub.get_text(strip=True).translate(sub_map))
    for sup in element.find_all(['sup', 'msup']): 
        sup.replace_with(sup.get_text(strip=True).translate(sup_map))

    for img in element.find_all('img'):
        src = img.get('src', '') or img.get('data-src', '')
        if not src: 
            img.decompose()
            continue
            
        url = ""
        b64 = ""
        if src.startswith('http'):
            url = src
        elif src.startswith('data:image'):
            try:
                if 'base64,' in src:
                    b64 = src.split('base64,')[1]
            except: pass
        else:
            decoded_src = urllib.parse.unquote(src)
            b64 = img_map.get(src) or img_map.get(decoded_src) or ""
            
        if b64 and not url:
            url = upload_to_imgbb(b64)
            
        if url:
            img.replace_with(f" img_s{url}img_e ")
        else:
            img.decompose()

    raw_text = element.get_text(separator=" ", strip=True)
    
    img_markers = []
    def img_repl(match):
        img_markers.append(match.group(0))
        return f" ZZZIMG{len(img_markers)-1}ZZZ "
        
    raw_text = re.sub(r'img_s.*?img_e', img_repl, raw_text)
    cleaned_text = aggressive_clean(raw_text)
    
    for i, marker in enumerate(img_markers):
        cleaned_text = cleaned_text.replace(f"ZZZIMG{i}ZZZ", marker)
        
    return re.sub(r'img_s(.*?)img_e', r'<img class="qimg" src="\1">', cleaned_text)

# --- ৩. WORKER SYSTEM ---
async def worker(worker_id):
    global is_processing
    while True:
        message, file_path, file_name = await processing_queue.get()
        is_processing = True
        try:
            await process_file(message, file_path, file_name)
        except Exception as e: 
            print(f"Error processing: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            is_processing = False
            processing_queue.task_done()

async def process_file(message, file_path, file_name):
    status_msg = await message.reply_text(f"🚀 **Starting:** `{file_name}`")
    img_map, html_body = {}, ""
    
    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    if file_name.endswith('.mhtml'):
        msg = email.message_from_bytes(file_bytes, policy=policy.default)
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
            elif part.get_content_type().startswith('image/'):
                loc, raw = part.get('Content-Location', ''), part.get_payload(decode=True)
                if loc and raw:
                    b64_data = base64.b64encode(raw).decode('utf-8')
                    img_map[loc] = b64_data
                    img_map[urllib.parse.unquote(loc)] = b64_data
    else:
        html_body = file_bytes.decode('utf-8', errors='ignore')

    soup = BeautifulSoup(html_body, 'html.parser')

    # --- CHORCHA.NET LOGIC ---
    chorcha_cards = soup.find_all('div', class_=lambda x: x and 'p-5' in x and 'rounded-xl' in x)
    
    if chorcha_cards:
        total_mcq = len(chorcha_cards)
        results = []
        start_time, last_ui = time.time(), time.time()
        
        for idx, card in enumerate(chorcha_cards, 1):
            q_div = card.find('div', class_=lambda x: x and 'font-medium' in x)
            if not q_div: continue
            q_text = re.sub(r'^\s*[0-9০-৯]+\s*[\.\)\-ঃ:]\s*', '', format_content(q_div, img_map))
            
            options, ans_idx = [], "1"
            ans_map = {'ক':'1','খ':'2','গ':'3','ঘ':'4'}
            
            for i, btn in enumerate(card.find_all('button', class_=lambda x: x and 'p-2' in x), 1):
                lbl = btn.find('span', class_=lambda x: x and 'rounded-full' in x)
                opt_content = btn.find('div', class_='flex-1')
                if opt_content:
                    options.append(format_content(opt_content, img_map))
                    if any(c in str(btn) for c in ['#017A47', 'border-[#017A47]', '#E2A03F', '#F59E0B', 'border-[#F59E0B]']):
                        ans_idx = ans_map.get(lbl.get_text(strip=True) if lbl else "", str(i))
                        
            while len(options) < 5: options.append("")
            if options[4].strip() and ans_idx == "5": options[3], ans_idx = options[4], "4"
            
            exp_div = card.find('div', class_=lambda x: x and 'prose' in x)
            exp_text = format_content(exp_div, img_map) if exp_div else ""
            
            results.append({"questions": q_text, "option1": options[0], "option2": options[1], "option3": options[2], "option4": options[3], "option5": "", "answer": ans_idx, "explanation": exp_text, "type": 1, "section": 1})
            
            if idx % 10 == 0 or idx == total_mcq:
                now = time.time()
                if now - last_ui > 7:
                    elapsed = now - start_time
                    eta = (elapsed / idx) * (total_mcq - idx)
                    try: await status_msg.edit_text(f"⌛ **ATLAS Dashboard (Chorcha)**\n📝 MCQ: `{idx}/{total_mcq}`\n⏳ ETA: `{int(eta//60):02d}:{int(eta%60):02d}`")
                    except: pass
                    last_ui = now
                    
        df = pd.DataFrame(results)
        csv_buf = io.BytesIO()
        df.to_csv(csv_buf, index=False, encoding='utf-8-sig')
        csv_buf.seek(0)
        csv_buf.name = f"ATLAS_Chorcha_{file_name}.csv"
        await message.reply_document(document=csv_buf, caption=f"✅ Task Done: {file_name}\n📊 Total: {len(results)}")
        await status_msg.delete(); gc.collect()
        return  

    # --- ORIGINAL TESTMOZ CODE ---
    cards = soup.find_all('div', class_=lambda x: x and 'rounded-lg' in x and 'shadow-md' in x)
    total_mcq = len(cards)
    results = []
    start_time, last_ui = time.time(), time.time()

    for idx, card in enumerate(cards, 1):
        q_p = card.find('p', class_='text-[17px]')
        q_text = re.sub(r'^\s*[0-9০-৯]+\s*[\.\)\-ঃ:]\s*', '', format_content(q_p, img_map)) if q_p else ""
        
        opt_divs = card.find_all('div', class_=lambda x: x and 'cursor-pointer' in x and 'col-span-2' in x)
        exp_div = card.find('div', class_=lambda x: x and 'col-span-2' in x and 'font-semibold' in x and 'cursor-pointer' not in x)

        for img in card.find_all('img'):
            if q_p and img in q_p.descendants: continue
            in_opt = any(img in opt.descendants for opt in opt_divs)
            in_exp = exp_div and img in exp_div.descendants
            if not in_opt and not in_exp:
                dummy = BeautifulSoup(str(img), 'html.parser')
                q_text += " " + format_content(dummy, img_map)

        options, ans_idx = [], "1"
        for i, opt in enumerate(opt_divs, 1):
            text_sm = opt.find('div', class_='text-sm')
            opt_text = format_content(text_sm, img_map) if text_sm else ""
            for img in opt.find_all('img'):
                if text_sm and img not in text_sm.descendants:
                    dummy = BeautifulSoup(str(img), 'html.parser')
                    opt_text += " " + format_content(dummy, img_map)
            options.append(opt_text)
            if opt.find('div', class_=lambda x: x and 'bg-green-500' in x) or opt.find('svg'): ans_idx = str(i)
        
        while len(options) < 5: options.append("")
        if options[4].strip() and ans_idx == "5": options[3], ans_idx = options[4], "4"
        
        exp_text = format_content(exp_div, img_map) if exp_div else ""
        results.append({"questions": q_text, "option1": options[0], "option2": options[1], "option3": options[2], "option4": options[3], "option5": "", "answer": ans_idx, "explanation": exp_text, "type": 1, "section": 1})
        
        if idx % 10 == 0 or idx == total_mcq:
            now = time.time()
            if now - last_ui > 7:
                elapsed = now - start_time
                eta = (elapsed / idx) * (total_mcq - idx)
                try:
                    await status_msg.edit_text(f"⌛ **ATLAS Dashboard**\n📝 MCQ: `{idx}/{total_mcq}`\n⏳ ETA: `{int(eta//60):02d}:{int(eta%60):02d}`")
                except: pass
                last_ui = now

    df = pd.DataFrame(results)
    csv_buf = io.BytesIO()
    df.to_csv(csv_buf, index=False, encoding='utf-8-sig')
    csv_buf.seek(0)
    csv_buf.name = f"ATLAS_{file_name}.csv"
    await message.reply_document(document=csv_buf, caption=f"✅ Task Done: {file_name}\n📊 Total: {len(results)}")
    await status_msg.delete(); gc.collect()

# --- ৪. PYROGRAM BOT APP ---
app = Client("atlas_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TELEGRAM_BOT_TOKEN, ipv6=False, workers=4)

@app.on_message(filters.document & filters.private)
async def handle_document(client, message):
    doc = message.document
    if not doc.file_name.endswith(('.html', '.mhtml')): return
    
    status_msg = await message.reply_text(f"🚀 Preparing to download `{doc.file_name}`...")
    start_time = time.time()
    
    try:
        file_path = await message.download(
            progress=progress,
            progress_args=(status_msg, start_time)
        )
        await status_msg.edit_text(f"✅ Download Complete!\n📦 Total Size: `{doc.file_size / (1024*1024):.2f} MB`\n⚙️ Starting Extraction...")
        
        await processing_queue.put((message, file_path, doc.file_name))
        pos = processing_queue.qsize()
        if pos > 0: 
            await message.reply_text(f"📥 Queue Position: {pos}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Download Error: {e}")

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text("ATLAS Bot Ready! Please Send Your mhtml/html File")

if __name__ == "__main__":
    print("="*40)
    print("🚀 ATLAS Ultimate Bot is Starting...")
    print("✅ Pyrogram Framework: Activated")
    print("✅ High-Speed Download: Enabled")
    print("✅ Twin-Worker System: Ready")
    print("✅ Anti-Doubling & Spacing Fix: Applied")
    print("="*40)
    print("⌛ Waiting for files...")
    
    loop = asyncio.get_event_loop()
    loop.create_task(worker(1))
    loop.create_task(worker(2)) 
    app.run()
