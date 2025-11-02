import streamlit as st
import pandas as pd
import random
import re
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DictionaryObject, NameObject, BooleanObject

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Across a Thousand Dead Worlds – Character Creator", layout="wide")

# ---------------- SESSION DEFAULTS ----------------
def sget(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

sget("rolled_background", None)
sget("rolled_life_event", None)
sget("rolled_earn_place", None)
sget("rolled_tic", None)
sget("rolled_coins", None)
sget("bg_bonus_opts", None)        # tuple(str,str)
sget("bg_bonus_choice", None)      # str
sget("bg_bonus_applied", False)    # bool

# ---------------- HELPERS ----------------
def load_csv(name):
    try:
        return pd.read_csv(name)
    except FileNotFoundError:
        st.warning(f"⚠️ Missing file: {name}")
        return pd.DataFrame()

def random_row(df):
    if df is None or len(df) == 0:
        return None
    return df.sample(1).iloc[0]

def parse_background_bonus(text: str):
    """
    Find 'Choose: +1 X or +1 Y' and return ('X','Y') or None.
    """
    if not isinstance(text, str):
        return None
    m = re.search(r"Choose:\s*\+1\s*(.*?)\s*or\s*\+1\s*(.*?)(?:[.。]|$)", text)
    if not m:
        return None
    return (m.group(1).strip(), m.group(2).strip())

def extract_background_title(text: str) -> str:
    """
    Extract the short title (e.g., 'Algae Farmer') from the full background line.
    """
    if not isinstance(text, str):
        return ""
    m = re.match(r"^\s*\d*\.?\s*([A-Za-zÀ-ÿ' -]+?)(?:\s*[-:–—]|$)", text)
    return m.group(1).strip() if m else text.split(" - ")[0].strip()

def add_need_appearances(writer: PdfWriter):
    try:
        catalog = writer._root_object
        if "/AcroForm" not in catalog:
            catalog[NameObject("/AcroForm")] = writer._add_object(DictionaryObject())
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    except Exception as e:
        print("⚠️ Could not set NeedAppearances:", e)

# ---------------- LOAD DATA ----------------
backgrounds = load_csv("backgrounds.csv")
life_events = load_csv("life_events.csv")
earn_place = load_csv("earn_place.csv")
tics = load_csv("nervous_tics.csv")
coins = load_csv("starting_coins.csv")
talents = load_csv("talents.csv")
drives = load_csv("drives.csv")
mannerisms = load_csv("mannerisms.csv")

# ---------------- UI ----------------
st.title("🚀 Across a Thousand Dead Worlds – Character Creator")
st.markdown("Create your Deep Diver and generate a filled character sheet PDF.")

# Basics
st.header("Step 1: Character Basics")
name = st.text_input("Character Name")

# Primary attributes
st.subheader("Primary Attributes (Rulebook Page 4)")
st.caption("Distribute 12 points among attributes (max 18).")
attribute_info = {
    "STR": "Strength – lifting, breaking, and raw power.",
    "DEX": "Dexterity – agility, precision, and coordination.",
    "CON": "Constitution – endurance, toughness, and resistance.",
    "WIL": "Will – mental fortitude and resolve.",
    "INT": "Intelligence – reasoning, logic, and understanding.",
    "CHA": "Charisma – charm, persuasion, and presence."
}
attrs, total_points, max_total = {}, 0, 18
cols = st.columns(6)
for i, a in enumerate(attribute_info):
    with cols[i]:
        v = st.slider(a, 0, 18, 0, key=f"attr_{a}", help=attribute_info[a])
        attrs[a] = v
        total_points += v
st.info(f"Attribute points used: {total_points}/{max_total}" + ("  ⚠️ OVER!" if total_points>max_total else ""))

# Secondary attributes (info)
with st.expander("📘 Secondary Attributes"):
    st.markdown("""
**Luck:** Start 3. Re-rolls or negate a killing blow (all Luck).  
**Stamina:** Start 10. Actions per round.  
**Stress:** Start 0. Mental strain.  
**Wounds:** Most PCs die at 3 Wounds.
""")

# Skills
st.subheader("Skills (Rulebook Pages 6–7)")
st.caption("Distribute 70 points among skills (max 10 per skill). Àrsaidh Technology starts at **-5**.")
skills_info = {
    "Àrsaidh Technology": "Hacking and comprehension of Àrsaidh systems. Starts at -5.",
    "Close Combat": "Melee fighting with knives, clubs, or wrenches.",
    "Manipulation": "Persuasion, negotiation, and intimidation.",
    "Medical Aid": "First aid, treating wounds, stabilizing allies.",
    "Perception": "Awareness of surroundings and hidden threats.",
    "Pilot": "Operation of vehicles and spacecraft.",
    "Ranged Combat": "Use of firearms and ranged weapons.",
    "Resolve": "Mental resilience under pressure.",
    "Science": "Understanding of biology, chemistry, and physics.",
    "Stealth": "Remaining unseen and unheard.",
    "Survival": "Enduring and navigating hostile environments.",
    "Technology": "Repairing and operating machinery or computers."
}
skills, total_skill_points = {}, 0
scols = st.columns(3)
for i, (sk, desc) in enumerate(skills_info.items()):
    with scols[i % 3]:
        if sk == "Àrsaidh Technology":
            val = st.slider(sk, -5, 10, -5, key=f"skill_{sk}", help=desc)
            cost = val + 5
        else:
            val = st.slider(sk, 0, 10, 0, key=f"skill_{sk}", help=desc)
            cost = val
        skills[sk] = val
        total_skill_points += cost
st.info(f"Skill points used: {total_skill_points}/70" + ("  ⚠️ OVER!" if total_skill_points>70 else ""))

# Talent
st.header("Step 2: Talent")
if not talents.empty:
    chosen_talent = st.selectbox("Choose your first Talent", talents["talent_name"].unique())
    st.write("🧠 **Description:**", talents.loc[talents["talent_name"]==chosen_talent, "talent_description"].iloc[0])
else:
    chosen_talent = ""
    st.warning("No talents.csv found.")

if st.button("🎲 Roll Random Talent"):
    t = random_row(talents)
    if t is not None:
        st.success(f"Random Talent: **{t['talent_name']}** – {t['talent_description']}")

# Drive
st.header("Step 3: Choose a Drive")
if not drives.empty:
    drive_name = st.selectbox("Drive", drives["drive_name"].tolist())
    st.write("💡 **Drive Description:**", drives.loc[drives["drive_name"]==drive_name, "drive_description"].values[0])
else:
    drive_name = ""

# Mannerisms
st.header("Step 4: Mannerisms")
mannerism_options = {}
if not mannerisms.empty:
    for cat in mannerisms["category"].unique():
        opts = mannerisms.loc[mannerisms["category"]==cat, "option"].tolist()
        mannerism_options[cat] = st.selectbox(f"When you are {cat.lower()}:", opts)
else:
    st.warning("No mannerisms.csv found.")

# Background & random details (+1 choice lives here)
st.header("Step 5: Background & Random Details")
c1, c2 = st.columns([1,2])
with c1:
    if st.button("🎲 Roll Background / Details"):
        bg = random_row(backgrounds)
        le = random_row(life_events)
        ep = random_row(earn_place)
        tic = random_row(tics)
        coin = random_row(coins)
        st.session_state.rolled_background = bg
        st.session_state.rolled_life_event = le
        st.session_state.rolled_earn_place = ep
        st.session_state.rolled_tic = tic
        st.session_state.rolled_coins = coin
        # reset background +1 state
        st.session_state.bg_bonus_applied = False
        st.session_state.bg_bonus_choice = None
        st.session_state.bg_bonus_opts = parse_background_bonus(bg["background"] if bg is not None else "")

with c2:
    bg = st.session_state.rolled_background
    le = st.session_state.rolled_life_event
    ep = st.session_state.rolled_earn_place
    tic = st.session_state.rolled_tic
    coin = st.session_state.rolled_coins

    if bg is not None:
        st.markdown(f"**Background:** {bg['background']}")
    if le is not None:
        st.markdown(f"**Life-Changing Event:** {le['life_event']}")
    if ep is not None:
        st.markdown(f"**Earned Place:** {ep['earn_place']}")
    if tic is not None:
        st.markdown(f"**Nervous Tic:** {tic['tic']}")
    if coin is not None:
        st.markdown(f"**Starting Coins:** {coin['coins']}")

# >>> Background +1 skill choice UI (re-added) <<<
if st.session_state.bg_bonus_opts:
    opt1, opt2 = st.session_state.bg_bonus_opts
    st.info(f"Background bonus: **Choose +1** to either **{opt1}** or **{opt2}** (free, does not count toward the 70 skill points).")
    # Keep previously chosen radio selection if any
    current_idx = 0
    if st.session_state.bg_bonus_choice in (opt1, opt2):
        current_idx = [opt1, opt2].index(st.session_state.bg_bonus_choice)
    selection = st.radio("Select your +1 skill bonus", [opt1, opt2], index=current_idx, horizontal=True)
    st.session_state.bg_bonus_choice = selection
    if st.button("✅ Apply Background Bonus"):
        st.session_state.bg_bonus_applied = True
        st.success(f"Background bonus queued: **+1 {selection}** (will appear on the PDF).")

# ---------------- GENERATE PDF ----------------
st.header("Step 6: Generate Character Sheet")

def skill_with_bonus(skill_name: str, base_value: int) -> int:
    if st.session_state.bg_bonus_applied and st.session_state.bg_bonus_choice == skill_name:
        return base_value + 1
    return base_value

if st.button("📜 Generate Character Sheet"):
    # If user never clicked Apply, default to the first option silently
    if (st.session_state.bg_bonus_opts is not None) and (not st.session_state.bg_bonus_applied):
        st.session_state.bg_bonus_choice = st.session_state.bg_bonus_opts[0]
        st.session_state.bg_bonus_applied = True

    bg = st.session_state.rolled_background
    le = st.session_state.rolled_life_event
    ep = st.session_state.rolled_earn_place
    tic = st.session_state.rolled_tic
    coin = st.session_state.rolled_coins

    # Build the fields dictionary
    fields = {
        "tf_name": str(name or ""),
        "tf_pa_str": str(attrs["STR"]),
        "tf_pa_dex": str(attrs["DEX"]),
        "tf_pa_con": str(attrs["CON"]),
        "tf_pa_wil": str(attrs["WIL"]),
        "tf_pa_int": str(attrs["INT"]),
        "tf_pa_cha": str(attrs["CHA"]),
        # Personality block mapping (title only for background)
        "tf_personality_background": str(extract_background_title(bg["background"])) if bg is not None else "",
        "tf_personality_earn-place": str(ep["earn_place"]) if ep is not None else "",
        "tf_personality_life-changing-event": str(le["life_event"]) if le is not None else "",
        "tf_personality_drive": str(drive_name or ""),
        "tf_talents-1": str(chosen_talent or ""),
        "tf_nervous-tic": str(tic["tic"]) if tic is not None else "",
        "tf_drake-coins": str(coin["coins"]) if coin is not None else "",
    }

    # Explicit skill field names to avoid any mismatch
    fields.update({
        "tf_talent_arsaidh-technology": str(skill_with_bonus("Àrsaidh Technology", skills["Àrsaidh Technology"])),
        "tf_talent_close-combat":     str(skill_with_bonus("Close Combat",      skills["Close Combat"])),
        "tf_talent_manipulation":     str(skill_with_bonus("Manipulation",      skills["Manipulation"])),
        "tf_talent_medical-aid":      str(skill_with_bonus("Medical Aid",       skills["Medical Aid"])),
        "tf_talent_perception":       str(skill_with_bonus("Perception",        skills["Perception"])),
        "tf_talent_pilot":            str(skill_with_bonus("Pilot",             skills["Pilot"])),
        "tf_talent_ranged-combat":    str(skill_with_bonus("Ranged Combat",     skills["Ranged Combat"])),
        "tf_talent_resolve":          str(skill_with_bonus("Resolve",           skills["Resolve"])),
        "tf_talent_science":          str(skill_with_bonus("Science",           skills["Science"])),
        "tf_talent_stealth":          str(skill_with_bonus("Stealth",           skills["Stealth"])),
        "tf_talent_survival":         str(skill_with_bonus("Survival",          skills["Survival"])),
        "tf_talent_technology":       str(skill_with_bonus("Technology",        skills["Technology"])),
    })

    # Add mannerisms
    for cat, val in mannerism_options.items():
        low = cat.lower()
        if "confident" in low:   fields["tf_traits_confident"]   = str(val)
        if "shy" in low:         fields["tf_traits_shy"]         = str(val)
        if "bored" in low:       fields["tf_traits_bored"]       = str(val)
        if "happy" in low:       fields["tf_traits_happy"]       = str(val)
        if "frustrated" in low:  fields["tf_traits_frustrated"]  = str(val)

    # Write PDF
    output = BytesIO()
    reader = PdfReader("Blank Character Sheet with fields.pdf")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
        writer.update_page_form_field_values(page, fields)
    add_need_appearances(writer)
    writer.write(output)
    output.seek(0)

    st.download_button(
        label="⬇️ Download Character Sheet",
        data=output,
        file_name=f"{name or 'Character'}_Sheet.pdf",
        mime="application/pdf"
    )
    st.success("✅ Character sheet generated successfully!")
