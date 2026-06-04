import os, re, pandas as pd, email, requests, base64, time, io, gc, asyncio, urllib.parse
from bs4 import BeautifulSoup
from email import policy
from PIL import Image
from pyrogram import Client, filters

# ============================================================
# 1. CONFIGURATION
# ============================================================
API_ID            = int(os.environ.get("API_ID", "33312774"))
API_HASH          = os.environ.get("API_HASH", "883db3366f8759d1d14c861c0d628232")
TELEGRAM_BOT_TOKEN= os.environ.get("BOT_TOKEN", "8741087357:AAFu-cAdnYAqfvCvZbX7gIATJMMRR8bLOVA")

API_KEYS = [
    "a74dc88809cedadda845003a16bb4bc7",
    "baaf0490e7c82522b8f21367a16bb4bc7",
    "10b5bc5469e5bf8c9d7f3565e44e7380",
    "1bbde6aba5711a01ee39da3fc678ce41",
    "7de311738b50e4036a8486f03cc2d2ed",
    "30cb522cec07fee7457baca2794c091b",
    "19fa44c34118d9ca97677e2a382af738",
    "eb13ca1318e16d04c27c1fa4f25b1b7a",
    "dbadcf0e1473dd969d7af3733ca284ca",
    "84d0a27d60e4878ece89ba4728b68453",
    "1dd490ff269fd720bf056d50d84a59df",
    "4c8e3794da096f6a91706f771a40f29a",
    "b425a5d3048db857641d546719289655",
    "8917b7773d570bc429f7d984d8154884",
]
current_key_index  = 0
exhausted_keys     = set()
processing_queue   = asyncio.Queue()
is_processing      = False

# ============================================================
# 2. UNICODE / LATEX MAPS
# ============================================================
SUP_MAP = str.maketrans("0123456789+-=()ni", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")
SUB_MAP = str.maketrans("0123456789+-=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")
SUP_TO_NORM = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

LATEX_SYMBOLS = {
    r'\\times':'×', r'\\div':'÷', r'\\cdot':'⋅', r'\\pm':'±', r'\\mp':'∓',
    r'\\leq':'≤', r'\\geq':'≥', r'\\neq':'≠', r'\\approx':'≈', r'\\equiv':'≡',
    r'\\cong':'≅', r'\\sim':'∼', r'\\ll':'≪', r'\\gg':'≫', r'\\propto':'∝',
    r'\\infty':'∞', r'\\partial':'∂', r'\\nabla':'∇', r'\\sum':'∑', r'\\prod':'∏',
    r'\\iiint':'∭', r'\\iint':'∬', r'\\oint':'∮', r'\\int':'∫',
    r'\\alpha':'α', r'\\beta':'β', r'\\gamma':'γ', r'\\Gamma':'Γ',
    r'\\Delta':'Δ', r'\\delta':'δ', r'\\epsilon':'ε', r'\\varepsilon':'ε',
    r'\\zeta':'ζ', r'\\eta':'η', r'\\theta':'θ', r'\\Theta':'Θ',
    r'\\kappa':'κ', r'\\lambda':'λ', r'\\Lambda':'Λ', r'\\mu':'μ',
    r'\\nu':'ν', r'\\xi':'ξ', r'\\pi':'π', r'\\Pi':'Π', r'\\rho':'ρ',
    r'\\sigma':'σ', r'\\Sigma':'Σ', r'\\tau':'τ', r'\\upsilon':'υ',
    r'\\phi':'φ', r'\\varphi':'φ', r'\\Phi':'Φ', r'\\chi':'χ',
    r'\\psi':'ψ', r'\\Psi':'Ψ', r'\\omega':'ω', r'\\Omega':'Ω',
    r'\\hbar':'ℏ', r'\\ell':'ℓ', r'\\Re':'ℜ', r'\\Im':'ℑ',
    r'\\rightleftharpoons':'⇌', r'\\rightleftarrows':'⇄',
    r'\\longrightarrow':'→', r'\\Longrightarrow':'⟹',
    r'\\rightarrow':'→', r'\\Rightarrow':'⇒',
    r'\\longleftarrow':'←', r'\\leftarrow':'←', r'\\Leftarrow':'⇐',
    r'\\leftrightarrow':'↔', r'\\Leftrightarrow':'⇔',
    r'\\uparrow':'↑', r'\\downarrow':'↓', r'\\mapsto':'↦', r'\\to':'→',
    r'\\in':'∈', r'\\notin':'∉', r'\\subset':'⊂', r'\\supset':'⊃',
    r'\\subseteq':'⊆', r'\\supseteq':'⊇', r'\\cup':'∪', r'\\cap':'∩',
    r'\\emptyset':'∅', r'\\setminus':'∖',
    r'\\wedge':'∧', r'\\vee':'∨', r'\\oplus':'⊕', r'\\otimes':'⊗',
    r'\\neg':'¬', r'\\lnot':'¬', r'\\forall':'∀', r'\\exists':'∃',
    r'\\therefore':'∴', r'\\because':'∵',
    r'\\parallel':'∥', r'\\perp':'⊥', r'\\angle':'∠',
    r'\\triangle':'△', r'\\square':'□', r'\\prime':'′',
    r'\\circ':'°', r'\\degree':'°', r'\\ast':'∗', r'\\bullet':'•',
    r'\\overline':'', r'\\bar':'', r'\\mathbb':'', r'\\mathrm':'',
    r'\\mathbf':'', r'\\text':'', r'\\left':'', r'\\right':'',
    r'\\,':' ', r'\\;':' ', r'\\:':' ', r'\\!'  :'',
    r'\\quad':' ', r'\\qquad':'  ',
}

COMMON_CHEMICALS = {
    'NAOH':'NaOH','HCL':'HCl','H2SO4':'H₂SO₄','NANO3':'NaNO₃',
    'CACL2':'CaCl₂','MGSO4':'MgSO₄','NABR':'NaBr','NACL':'NaCl',
    'NAHCO3':'NaHCO₃','KMN04':'KMnO₄','CACO3':'CaCO₃','NA2CO3':'Na₂CO₃',
    'CA(OH)2':'Ca(OH)₂','FE2O3':'Fe₂O₃','AL2O3':'Al₂O₃',
}

# ============================================================
# 3. IMAGE UTILS
# ============================================================
def compress_image(b64_str):
    try:
        img = Image.open(io.BytesIO(base64.b64decode(b64_str)))
        if img.mode in ("RGBA","P"): img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", optimize=True, quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except: return b64_str

def upload_to_imgbb(b64):
    global current_key_index, exhausted_keys
    if not b64: return ""
    compressed = compress_image(b64)
    for _ in range(len(API_KEYS)):
        key = API_KEYS[current_key_index]
        try:
            res = requests.post("https://api.imgbb.com/1/upload",
                                data={"key": key, "image": compressed}, timeout=12)
            if res.status_code == 200:
                return res.json()['data']['url']
            if res.status_code in (400, 429):
                exhausted_keys.add(current_key_index)
            current_key_index = (current_key_index + 1) % len(API_KEYS)
        except:
            current_key_index = (current_key_index + 1) % len(API_KEYS)
    return ""

# ============================================================
# 4. PROGRESS
# ============================================================
async def progress(current, total, message, start_time):
    now  = time.time()
    diff = now - start_time
    if diff < 1: return
    speed   = current / diff if diff > 0 else 0
    eta     = (total - current) / speed if speed > 0 else 0
    cur_mb  = current / 1048576
    tot_mb  = total   / 1048576
    spd_mb  = speed   / 1048576
    try:
        if int(diff) % 5 == 0:
            await message.edit_text(
                f"📥 **Downloading File**\n\n"
                f"📊 **Size:** `{cur_mb:.2f}/{tot_mb:.2f} MB`\n"
                f"🚀 **Speed:** `{spd_mb:.2f} MB/s`\n"
                f"⏳ **ETA:** `{int(eta//60):02d}:{int(eta%60):02d}`"
            )
    except: pass

# ============================================================
# 5. CLEAN / CONVERT ENGINE
# ============================================================
def convert_to_english_numbers(text):
    return text.translate(str.maketrans("০১২৩৪৫৬৭৮৯","0123456789"))

def latex_to_unicode(text):
    """Convert LaTeX → Unicode. HTML only for fraction/matrix (compact)."""
    for k, v in LATEX_SYMBOLS.items():
        text = re.sub(k, v, text)
    # sqrt
    text = re.sub(r'\\sqrt\s*\{([^{}]+)\}', r'√(\1)', text)
    text = text.replace('\\sqrt','√')
    # frac → compact html
    text = re.sub(r'\\[dt]?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}',
                  lambda m: f"<sup>{m.group(1)}</sup>⁄<sub>{m.group(2)}</sub>", text)
    # nested frac plain: d/1+√q₂/q₁ → d/(1+√q₂/q₁)
    text = re.sub(r'([a-zA-Z\d])/([^/\s]{3,})',
                  lambda m: f"{m.group(1)}/({m.group(2)})"
                  if '/' in m.group(2) else m.group(0), text)
    # ^{...} _{...}
    text = re.sub(r'\^\{([^{}]+)\}', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'_\{([^{}]+)\}', lambda m: m.group(1).translate(SUB_MAP), text)
    # ^x _x single char
    text = re.sub(r'\^([0-9a-zA-Z+\-=()])', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'_([0-9a-zA-Z+\-=()])', lambda m: m.group(1).translate(SUB_MAP), text)
    # hat{i/j/k} — MUST before vec
    text = re.sub(r'\\hat\s*\{?\s*([ijkn])\s*\}?',
                  lambda m: {'i':'î','j':'ĵ','k':'k̂','n':'n̂'}[m.group(1)], text)
    return text

def fix_vectors(text):
    # hat[ijk] (no boundary needed — works inside words like hati)
    text = re.sub(r'hat([ijk])', lambda m: {'i':'î','j':'ĵ','k':'k̂'}[m.group(1)], text)
    # \vec{x} and vecX
    text = re.sub(r'\\vec\s*\{?([a-zA-Z])\}?', r'\1⃗', text)
    text = re.sub(r'\bvec([a-zA-Z])\b', r'\1⃗', text)
    # number/sign + bare i/j/k → unit vector (not part of a word)
    text = re.sub(r'([-−]?\d*\.?\d+)\s*([ijk])\b(?![a-zA-Z\u0980-\u09FF])',
                  lambda m: m.group(1)+{'i':'î','j':'ĵ','k':'k̂'}[m.group(2)], text)
    return text

def fix_sci_notation(text):
    # ×¹⁰XYZ → ×10XYZ  (superscript 1 and 0 wrongly placed)
    text = re.sub(r'×¹⁰([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]*)', lambda m: f"×10{m.group(1)}", text)
    # ×10 followed by gap + sup digits
    text = re.sub(r'(×10)\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+)', r'\1\2', text)
    # ×10 + unicode minus/dash + digits
    text = re.sub(r'(×10)\s*[−–]\s*([⁰¹²³⁴⁵⁶⁷⁸⁹]+)', r'\1⁻\2', text)
    # ×10 + ascii minus + digits
    text = re.sub(r'(×10)\s*-\s*(\d+)',
                  lambda m: f"{m.group(1)}⁻{''.join(c.translate(SUP_MAP) for c in m.group(2))}", text)
    # ×10 + space + plain digits (e.g. ×10 23)
    text = re.sub(r'(×10)\s+(\d+)',
                  lambda m: f"{m.group(1)}{''.join(c.translate(SUP_MAP) for c in m.group(2))}", text)
    # NmC-2 or NmC−2 at end of sci unit → NmC⁻²
    text = re.sub(r'([A-Za-z])[-−](\d)', lambda m: m.group(1)+'⁻'+m.group(2).translate(SUP_MAP), text)
    return text

def fix_degrees(text):
    text = text.replace('∘','°').replace('^\\circ','°').replace('^{\\circ}','°')
    # 90 o → 90°
    text = re.sub(r'(\d)\s+o\b', r'\1°', text)
    # 150 ° → 150°
    text = re.sub(r'(\d)\s+°', r'\1°', text)
    # 120°15' no gap
    text = re.sub(r'°\s+(\d+\')', r'°\1', text)
    text = text.replace('° C','°C').replace('° c','°c')
    # superscript degrees that got wrongly converted: ⁰ at end of number
    text = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹]+)°',
                  lambda m: m.group(1).translate(SUP_TO_NORM)+'°', text)
    return text

def fix_power_after_letter(text):
    # E∝r2 → E∝r²  (bare digit after letter, not part of formula already processed)
    text = re.sub(r'(?<=[a-zA-Z])(\d+)(?![a-zA-Z₀-₉⁰-⁹\u0980-\u09FF])',
                  lambda m: m.group(1).translate(SUP_MAP), text)
    return text

def fix_chemical_misc(text):
    # Common all-caps chemical names
    for wrong, right in COMMON_CHEMICALS.items():
        text = re.sub(rf'\b{wrong}\b', right, text, flags=re.IGNORECASE)
    # [Cr(CN)₆ ]³⁻ → [Cr(CN)₆]³⁻
    text = re.sub(r'\s+\]', ']', text)
    text = re.sub(r'\[\s+', '[', text)
    # 0.1MHCI → 0.1M HCI (concentration unit before element)
    text = re.sub(r'(\d+\.?\d*)(M)([A-Z])', r'\1\2 \3', text)
    # [NH4+/[NH⁴⁺ variants → [NH₄⁺]
    text = re.sub(r'\[NH[⁴4₄]\s*[⁺+]\s*(?!\])', '[NH₄⁺]', text)
    # 10×10⁻¹ type: bare digit exponent after ×10
    text = re.sub(r'(×10)([0-9])\b',
                  lambda m: f"{m.group(1)}{m.group(2).translate(SUP_MAP)}", text)
    return text

def fix_spacing(text):
    # sub/sup chars no leading space
    text = re.sub(r'\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎]+)', r'\1', text)
    # element + charge/power no space: Cu ²⁺ → Cu²⁺
    text = re.sub(r'([A-Z][a-z]?)\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼]+)', r'\1\2', text)
    # subscript + capital: H₂ O → H₂O
    text = re.sub(r'([₀₁₂₃₄₅₆₇₈₉])\s+(?=[A-Z])', r'\1', text)
    # digit + capital (chemical): 2H₂ + no gap lost
    text = re.sub(r'(?<=\d)\s+(?=[A-Z][a-z])', '', text)
    # bracket space
    text = re.sub(r'\s+\]', ']', text)
    text = re.sub(r'\[\s+', '[', text)
    # dot gaps
    text = text.replace(' . ','.').replace(' .','.')
    return text

def fix_doubling(text):
    """Remove duplicated expressions (same text appearing twice in a row)."""
    # Pattern: any string followed immediately by itself (with optional space/punct)
    text = re.sub(r'(.{6,}?)\s*\1', r'\1', text)
    return text

def aggressive_clean(text):
    if not text: return ""
    text = convert_to_english_numbers(text)
    text = latex_to_unicode(text)
    text = fix_vectors(text)
    text = fix_sci_notation(text)
    text = fix_degrees(text)
    text = fix_power_after_letter(text)
    text = fix_chemical_misc(text)
    # legacy raw LaTeX cleanup (fallback)
    text = re.sub(r'_\{\s*([^}]+)\s*\}', lambda m: m.group(1).translate(SUB_MAP), text)
    text = re.sub(r'\^\{\s*([^}]+)\s*\}', lambda m: m.group(1).translate(SUP_MAP), text)
    text = re.sub(r'_([0-9a-zA-Z+-]+)', lambda m: m.group(1).translate(SUB_MAP), text)
    text = re.sub(r'\^([0-9a-zA-Z+-]+)', lambda m: m.group(1).translate(SUP_MAP), text)
    # sub letters back to normal where wrong (NₐHCO₃ → NaHCO₃)
    text = text.translate(str.maketrans("ₐₑₒₓₕₖₗₘₙₚₛₜ","aeoxhklmnpst"))
    text = text.replace('₍','(').replace('₎',')')
    # units spacing
    units = r'(mL|L|m³|cm³|g|kg|mol|M|Pa|atm|J|K|V|A|W|N|C|Hz|eV|nm|mm|cm|m)'
    text = re.sub(r'(\d+)\s*'+units+r'\b', r'\1 \2', text)
    text = fix_spacing(text)
    # Fix: k̂̂ double hat from overlapping rules
    text = re.sub(r'k̂\u0302', 'k̂', text)
    text = re.sub(r'î\u0302',  'î', text)
    text = re.sub(r'ĵ\u0302',  'ĵ', text)
    # Fix: degree trailing space before ) , ;
    text = re.sub(r'°\s+\)', '°)', text)
    text = re.sub(r'°\s+([,;])', r'°\1', text)
    # Fix: 0.1 M HCI → 0.1M HCI (molarity no space)
    text = re.sub(r'(\d)\s+(M)\s+([A-Z])', r'\1\2 \3', text)
    text = fix_doubling(text)
    # remove leftover latex macros & braces (protect html tags)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    text = re.sub(r'(?<![a-zA-Z<>/="])[{}](?![a-zA-Z<>/="])', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_matrix_html(rows):
    cells = "".join("<tr>"+"".join(f"<td>{c}</td>" for c in r)+"</tr>" for r in rows)
    return f"<table border=1>{cells}</table>"

# ============================================================
# 6. FORMAT CONTENT (HTML element → clean string)
# ============================================================
def format_content(element, img_map):
    if not element: return ""

    # --- Remove ALL duplicate/hidden math spans ---
    for tag in element.find_all(['annotation','script']):
        tag.decompose()
    for cls in ['katex-mathml','MJX_Assistive_MathML','MathJax_Preview',
                'MathJax_SVG_Hidden','screenreader-only']:
        for s in element.find_all(True, class_=cls):
            s.decompose()
    # Unwrap katex-html (keep visual content, remove wrapper)
    for s in element.find_all('span', class_='katex-html'):
        s.unwrap()
    # Remove MathJax processed duplicates
    for s in element.find_all('span', class_=re.compile(r'MathJax')):
        s.decompose()

    # --- HTML <table> → compact matrix ---
    for tbl in element.find_all('table'):
        rows = []
        for tr in tbl.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
            if cells: rows.append(cells)
        if rows:
            enc = base64.b64encode(build_matrix_html(rows).encode()).decode()
            tbl.replace_with(f" MTRXSTART{enc}MTRXEND ")

    # --- mfrac → fraction html ---
    for mfrac in element.find_all('mfrac'):
        c = mfrac.find_all(recursive=False)
        if len(c) == 2:
            mfrac.replace_with(f"<sup>{c[0].get_text(strip=True)}</sup>⁄<sub>{c[1].get_text(strip=True)}</sub>")

    # --- sub/sup HTML tags ---
    for sub in element.find_all(['sub','msub']):
        sub.replace_with(sub.get_text(strip=True).translate(SUB_MAP))
    for sup in element.find_all(['sup','msup']):
        sup.replace_with(sup.get_text(strip=True).translate(SUP_MAP))

    # --- images ---
    for img in element.find_all('img'):
        src = img.get('src','') or img.get('data-src','')
        if not src: img.decompose(); continue
        url = b64 = ""
        if src.startswith('http'):
            url = src
        elif src.startswith('data:image'):
            if 'base64,' in src: b64 = src.split('base64,')[1]
        else:
            dec = urllib.parse.unquote(src)
            b64 = img_map.get(src) or img_map.get(dec) or ""
        if b64 and not url: url = upload_to_imgbb(b64)
        if url: img.replace_with(f" img_s{url}img_e ")
        else:   img.decompose()

    raw = element.get_text(separator=" ", strip=True)

    # Protect matrix blocks
    matrix_blocks = []
    def mtrx_repl(m):
        matrix_blocks.append(base64.b64decode(m.group(1)).decode())
        return f" ZZZMTRX{len(matrix_blocks)-1}ZZZ "
    raw = re.sub(r'MTRXSTART(.*?)MTRXEND', mtrx_repl, raw)

    # LaTeX \begin{matrix} → html protect
    def latex_mtrx(m):
        body = m.group(1)
        rows = [r.strip() for r in re.split(r'\\\\|\n', body) if r.strip()]
        grid = [[c.strip() for c in r.split('&')] for r in rows]
        matrix_blocks.append(build_matrix_html(grid))
        return f" ZZZMTRX{len(matrix_blocks)-1}ZZZ "
    raw = re.sub(r'\\begin\{[bp]?matrix\}(.*?)\\end\{[bp]?matrix\}', latex_mtrx, raw, flags=re.DOTALL)

    # Protect image markers
    img_markers = []
    def img_repl(m):
        img_markers.append(m.group(0))
        return f" ZZZIMG{len(img_markers)-1}ZZZ "
    raw = re.sub(r'img_s.*?img_e', img_repl, raw)

    cleaned = aggressive_clean(raw)

    for i, blk in enumerate(matrix_blocks):
        cleaned = cleaned.replace(f"ZZZMTRX{i}ZZZ", blk)
    for i, marker in enumerate(img_markers):
        cleaned = cleaned.replace(f"ZZZIMG{i}ZZZ", marker)

    return re.sub(r'img_s(.*?)img_e', r'<img class="qimg" src="\1">', cleaned)

# ============================================================
# 7. LIVE DASHBOARD
# ============================================================
def imgbb_status():
    total = len(API_KEYS)
    used  = len(exhausted_keys)
    ok    = total - used
    return f"🗝 ImgBB: {ok}/{total} keys active"

async def update_dashboard(status_msg, file_name, idx, total, img_count, start_time, site="ATLAS"):
    now     = time.time()
    elapsed = now - start_time
    eta     = (elapsed / idx) * (total - idx) if idx > 0 else 0
    h, rem  = divmod(int(elapsed), 3600)
    m, s    = divmod(rem, 60)
    eh,erem = divmod(int(eta), 3600)
    em, es  = divmod(erem, 60)
    done_pct= int(idx/total*100) if total > 0 else 0
    bar_len = 10
    filled  = int(bar_len * idx / total) if total > 0 else 0
    bar     = "█"*filled + "░"*(bar_len-filled)
    try:
        await status_msg.edit_text(
            f"⚙️ **{site} Dashboard**\n"
            f"📄 `{file_name}`\n\n"
            f"[{bar}] {done_pct}%\n"
            f"📝 MCQ: `{idx}/{total}`\n"
            f"🖼 Images: `{img_count}`\n"
            f"⏱ Elapsed: `{h:02d}:{m:02d}:{s:02d}`\n"
            f"⏳ ETA: `{eh:02d}:{em:02d}:{es:02d}`\n"
            f"{imgbb_status()}"
        )
    except: pass

# ============================================================
# 8. WORKER SYSTEM
# ============================================================
async def worker(worker_id):
    global is_processing
    while True:
        message, file_path, file_name = await processing_queue.get()
        is_processing = True
        try:
            await process_file(message, file_path, file_name)
        except Exception as e:
            print(f"Worker error: {e}")
        finally:
            if os.path.exists(file_path): os.remove(file_path)
            is_processing = False
            processing_queue.task_done()

# ============================================================
# 9. PROCESS FILE
# ============================================================
async def process_file(message, file_path, file_name):
    status_msg = await message.reply_text(f"🚀 **Starting:** `{file_name}`")
    img_map, html_body = {}, ""
    img_count = [0]

    # Patch upload_to_imgbb to count images
    orig_upload = upload_to_imgbb
    def counting_upload(b64):
        url = orig_upload(b64)
        if url: img_count[0] += 1
        return url

    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    if file_name.endswith('.mhtml'):
        msg = email.message_from_bytes(file_bytes, policy=policy.default)
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/html':
                html_body = part.get_payload(decode=True).decode(
                    part.get_content_charset() or 'utf-8', errors='ignore')
            elif ct.startswith('image/'):
                loc = part.get('Content-Location','')
                raw = part.get_payload(decode=True)
                if loc and raw:
                    b64d = base64.b64encode(raw).decode()
                    img_map[loc] = b64d
                    img_map[urllib.parse.unquote(loc)] = b64d
    else:
        html_body = file_bytes.decode('utf-8', errors='ignore')

    soup = BeautifulSoup(html_body, 'html.parser')

    # ---- CHORCHA.NET ----
    chorcha_cards = soup.find_all('div', class_=lambda x: x and 'p-5' in x and 'rounded-xl' in x)
    if chorcha_cards:
        total_mcq  = len(chorcha_cards)
        results    = []
        start_time = time.time()
        last_ui    = 0.0
        ans_map    = {'ক':'1','খ':'2','গ':'3','ঘ':'4'}

        for idx, card in enumerate(chorcha_cards, 1):
            q_div = card.find('div', class_=lambda x: x and 'font-medium' in x)
            if not q_div: continue
            q_text = re.sub(r'^\s*[0-9০-৯]+\s*[\.\)\-ঃ:]\s*','', format_content(q_div, img_map))

            options, ans_idx = [], "1"
            for i, btn in enumerate(card.find_all('button', class_=lambda x: x and 'p-2' in x), 1):
                lbl = btn.find('span', class_=lambda x: x and 'rounded-full' in x)
                opt_c = btn.find('div', class_='flex-1')
                if opt_c:
                    options.append(format_content(opt_c, img_map))
                    if any(c in str(btn) for c in ['#017A47','border-[#017A47]','#E2A03F','#F59E0B','border-[#F59E0B]']):
                        ans_idx = ans_map.get(lbl.get_text(strip=True) if lbl else "", str(i))

            while len(options) < 5: options.append("")
            if options[4].strip() and ans_idx=="5": options[3], ans_idx = options[4], "4"

            exp_div  = card.find('div', class_=lambda x: x and 'prose' in x)
            exp_text = format_content(exp_div, img_map) if exp_div else ""

            results.append({"questions":q_text,"option1":options[0],"option2":options[1],
                            "option3":options[2],"option4":options[3],"option5":"",
                            "answer":ans_idx,"explanation":exp_text,"type":1,"section":1})

            now = time.time()
            if idx % 5 == 0 or idx == total_mcq:
                if now - last_ui > 5:
                    await update_dashboard(status_msg, file_name, idx, total_mcq,
                                           img_count[0], start_time, "Chorcha")
                    last_ui = now

        df = pd.DataFrame(results)
        buf = io.BytesIO()
        df.to_csv(buf, index=False, encoding='utf-8-sig', lineterminator='\n')
        buf.seek(0); buf.name = f"ATLAS_Chorcha_{file_name}.csv"
        await message.reply_document(document=buf,
            caption=f"✅ Done: `{file_name}`\n📊 Total MCQ: `{len(results)}`\n🖼 Images: `{img_count[0]}`")
        await status_msg.delete(); gc.collect(); return

    # ---- TESTMOZ ----
    cards     = soup.find_all('div', class_=lambda x: x and 'rounded-lg' in x and 'shadow-md' in x)
    total_mcq = len(cards)
    results   = []
    start_time= time.time()
    last_ui   = 0.0

    for idx, card in enumerate(cards, 1):
        q_p    = card.find('p', class_='text-[17px]')
        q_text = re.sub(r'^\s*[0-9০-৯]+\s*[\.\)\-ঃ:]\s*','',
                        format_content(q_p, img_map)) if q_p else ""

        opt_divs = card.find_all('div', class_=lambda x: x and 'cursor-pointer' in x and 'col-span-2' in x)
        exp_div  = card.find('div', class_=lambda x: x and 'col-span-2' in x
                             and 'font-semibold' in x and 'cursor-pointer' not in x)

        for img in card.find_all('img'):
            if q_p and img in q_p.descendants: continue
            if any(img in opt.descendants for opt in opt_divs): continue
            if exp_div and img in exp_div.descendants: continue
            dummy   = BeautifulSoup(str(img), 'html.parser')
            q_text += " " + format_content(dummy, img_map)

        options, ans_idx = [], "1"
        for i, opt in enumerate(opt_divs, 1):
            text_sm  = opt.find('div', class_='text-sm')
            opt_text = format_content(text_sm, img_map) if text_sm else ""
            for img in opt.find_all('img'):
                if text_sm and img not in text_sm.descendants:
                    dummy     = BeautifulSoup(str(img), 'html.parser')
                    opt_text += " " + format_content(dummy, img_map)
            options.append(opt_text)
            if opt.find('div', class_=lambda x: x and 'bg-green-500' in x) or opt.find('svg'):
                ans_idx = str(i)

        while len(options) < 5: options.append("")
        if options[4].strip() and ans_idx=="5": options[3], ans_idx = options[4], "4"

        exp_text = format_content(exp_div, img_map) if exp_div else ""
        results.append({"questions":q_text,"option1":options[0],"option2":options[1],
                        "option3":options[2],"option4":options[3],"option5":"",
                        "answer":ans_idx,"explanation":exp_text,"type":1,"section":1})

        now = time.time()
        if idx % 5 == 0 or idx == total_mcq:
            if now - last_ui > 5:
                await update_dashboard(status_msg, file_name, idx, total_mcq,
                                       img_count[0], start_time, "ATLAS")
                last_ui = now

    df = pd.DataFrame(results)
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding='utf-8-sig', lineterminator='\n')
    buf.seek(0); buf.name = f"ATLAS_{file_name}.csv"
    await message.reply_document(document=buf,
        caption=f"✅ Done: `{file_name}`\n📊 Total MCQ: `{len(results)}`\n🖼 Images: `{img_count[0]}`")
    await status_msg.delete(); gc.collect()

# ============================================================
# 10. BOT HANDLERS
# ============================================================
app = Client("atlas_bot", api_id=API_ID, api_hash=API_HASH,
             bot_token=TELEGRAM_BOT_TOKEN, ipv6=False, workers=4)

@app.on_message(filters.document & filters.private)
async def handle_document(client, message):
    doc = message.document
    if not doc.file_name.endswith(('.html','.mhtml')): return
    status_msg = await message.reply_text(f"📥 Preparing: `{doc.file_name}`...")
    start = time.time()
    try:
        file_path = await message.download(progress=progress, progress_args=(status_msg, start))
        await status_msg.edit_text(
            f"✅ Downloaded: `{doc.file_size/1048576:.2f} MB`\n⚙️ Processing...")
        await processing_queue.put((message, file_path, doc.file_name))
        pos = processing_queue.qsize()
        if pos > 1:
            await message.reply_text(f"⏳ Queue position: `{pos}`")
    except Exception as e:
        await status_msg.edit_text(f"❌ Download error: {e}")

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "🤖 **ATLAS Bot Ready!**\n\n"
        "📤 Send your `.mhtml` or `.html` file to extract MCQs.\n\n"
        f"🗝 ImgBB Keys: `{len(API_KEYS)} active`\n"
        f"⚙️ Workers: `2 parallel`"
    )

# ============================================================
# 11. MAIN
# ============================================================
if __name__ == "__main__":
    print("="*45)
    print("🚀 ATLAS Ultimate Bot is Starting...")
    print("✅ Pyrogram Framework: Activated")
    print("✅ High-Speed Download: Enabled")
    print("✅ Twin-Worker System: Ready")
    print("✅ LaTeX→Unicode + Matrix + Vector: Applied")
    print("✅ Anti-Doubling & Spacing Fix: Applied")
    print("✅ Live Premium Dashboard: Active")
    print("="*45)
    print("⌛ Waiting for files...")

    loop = asyncio.get_event_loop()
    loop.create_task(worker(1))
    loop.create_task(worker(2))
    app.run()
