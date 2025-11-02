import streamlit as st
import pandas as pd
import random
import re
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DictionaryObject, NameObject, BooleanObject
from io import BytesIO

# ---------- CONFIG ----------
st.set_page_config(page_title="Across a Thousand Dead Worlds – Character Creator", layout="wide")

# ---------- SESSION DEFAULTS ----------
def sget(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

sget("rolled_background", None)
sget("rolled_life_event", None)
sget("rolled_earn_place", None)
sget("rolled_tic", None)
sget("rolled_coins", None)
sget("bg_bonus_opts", None)
sget("bg_bonus_choice", None)
sget("bg_bonus_applied", False)

# ---------- HELPERS ----------
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

def parse_background_bonus(text):
    if not isinstance(text, str):
        return None
    m = re.search(r"Choose:\s*\+1\s*(.*?)\s*or\s*\+1\s*(.*?)(?:\.|$)", text)
    if not m:
        return None
    return (m.group(1).strip(), m.group(2).strip())

def add_need_appearances(writer: PdfWriter):
    try:
        catalog = writer._root_object
        if "/AcroForm" not in catalog:
            catalog[NameObject("/AcroForm")] = writer._add_object(DictionaryObject())
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    except Exception as e:
        print("⚠️ Could not set NeedAppearances:", e)

# Extract clean title from background description
def extract_background_title(text):
    if not isinstance(text, str):
        return ""
    # Removes numbering (e.g., "1.") and captures text up to punctuation
    m = re.match(r"^\s*\d*\.*\s*([A-Za-z\s']+?)(?:[.:,-]|\s*$)", text)
    if m:
        return m.group(1).strip()
    # Fallback: first 4 words if no punctuation
    return " ".join(text.split()[:4]).strip()

# ---------- LOAD DATA ----------
backgrounds = load_csv("backgrounds.csv")
life_events = load_csv("life_events.csv")
earn_place = load_csv("earn_place.csv")
tics = load_csv("nervous_tics.csv")
coins = load_csv("starting_coins.csv")
talents = load_csv("talents.csv")
drives = load_csv("drives.csv")
mannerisms = load_csv("mannerisms.csv")

# ---------- HEADER ----------
st.title("🚀 Across a Thousand Dead Worlds – Character Creator")
st.markdown("Create your Deep Diver and generate a filled character sheet PDF.")

# ---------- CHARACTER BASICS ----------
st.header("Step 1: Character Basics")
name = st.text_input("Character Name")

# ---------- PRIMARY ATTRIBUTES ----------
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

attrs = {}
attr_cols = st.columns(6)
max_total = 18
total_points = 0

for i, label in enumerate(attribute_info.keys()):
    with attr_cols[i]:
        val = st.slider(label, 0, 18, 0, key=f"attr_{label}", help=attribute_info[label])
        attrs[label] = val
        total_points += val

if total_points > max_total:
    st.error(f"⚠️ Total exceeds {max_total}! Currently: {total_points}")
else:
    st.info(f"Attribute points used: {total_points}/{max_total}")

# ---------- SECONDARY ATTRIBUTES ----------
with st.expander("📘 Secondary Attributes"):
    st.markdown("""
**Luck:** Re-rolls and near-death negation (start 3).  
**Stamina:** Actions per round (start 10).  
**Stress:** Mental strain (start 0).  
**Wounds:** Physical damage capacity (max 3 before death).
""")

# ---------- SKILLS ----------
st.subheader("Skills (Rulebook Pages 6–7)")
st.caption("Distribute 70 points among skills (max 10 per skill).")

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

skills = {}
total_skill_points = 0
skill_cols = st.columns(3)

for i, (skill, desc) in enumerate(skills_info.items()):
    with skill_cols[i % 3]:
        if skill == "Àrsaidh Technology":
            val = st.slider(skill, -5, 10, -5, key=f"skill_{skill}", help=desc)
            cost = val + 5
        else:
            val = st.slider(skill, 0, 10, 0, key=f"skill_{skill}", help=desc)
            cost = val
        skills[skill] = val
        total_skill_points += cost

if total_skill_points > 70:
    st.error(f"⚠️ Total exceeds 70! Currently: {total_skill_points}")
else:
    st.info(f"Skill points used: {total_skill_points}/70")

# ---------- TALENT ----------
st.header("Step 2: Talent")
if len(talents) > 0:
    chosen_talent = st.selectbox("Choose your first Talent", talents["talent_name"].unique())
    desc = talents.loc[talents["talent_name"] == chosen_talent, "talent_description"].iloc[0]
    st.write(f"🧠 **Description:** {desc}")
else:
    chosen_talent = ""
    st.warning("No talents.csv found.")

if st.button("🎲 Roll Random Talent"):
    t = random_row(talents)
    if t is not None:
        st.success(f"Random Talent: **{t['talent_name']}** – {t['talent_description']}")

# ---------- DRIVE ----------
st.header("Step 3: Choose a Drive")
if len(drives) > 0:
    drive_name = st.selectbox("Drive", drives["drive_name"].tolist())
    desc = drives.loc[drives["drive_name"] == drive_name, "drive_description"].values[0]
    st.write(f"💡 **Drive Description:** {desc}")
else:
    drive_name = ""

# ---------- MANNERISMS ----------
st.header("Step 4: Mannerisms")
mannerism_options = {}
if not mannerisms.empty:
    categories = mannerisms["category"].unique()
    for cat in categories:
        opts = mannerisms.loc[mannerisms["category"] == cat, "option"].tolist()
        mannerism_options[cat] = st.selectbox(f"When you are {cat.lower()}:", opts)
else:
    st.warning("No mannerisms.csv found.")

# ---------- STEP 5A: BACKGROUND & BONUS ----------
st.header("Step 5: Background & Random Details")

colA, colB = st.columns([1, 2])
with colA:
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
        st.session_state.bg_bonus_applied = False
        st.session_state.bg_bonus_choice = None
        st.session_state.bg_bonus_opts = parse_background_bonus(bg["background"] if bg is not None else "")

with colB:
    bg = st.session_state.rolled_background
    if bg is not None:
        st.markdown(f"**Background:** {bg['background']}")
    le = st.session_state.rolled_life_event
    if le is not None:
        st.markdown(f"**Life-Changing Event:** {le['life_event']}")
    ep = st.session_state.rolled_earn_place
    if ep is not None:
        st.markdown(f"**Earned Place:** {ep['earn_place']}")
    tic = st.session_state.rolled_tic
    if tic is not None:
        st.markdown(f"**Nervous Tic:** {tic['tic']}")
    coin = st.session_state.rolled_coins
    if coin is not None:
        st.markdown(f"**Starting Coins:** {coin['coins']}")

# ---------- GENERATE PDF ----------
st.header("Step 6: Generate Character Sheet")

def skill_with_bonus(skill_name, base_value):
    if st.session_state.bg_bonus_applied and st.session_state.bg_bonus_choice == skill_name:
        return base_value + 1
    return base_value

if st.button("📜 Generate Character Sheet"):
    bg = st.session_state.rolled_background
    le = st.session_state.rolled_life_event
    ep = st.session_state.rolled_earn_place
    tic = st.session_state.rolled_tic
    coin = st.session_state.rolled_coins

    fields = {
        "tf_name": str(name or ""),
        "tf_pa_str": str(attrs["STR"]),
        "tf_pa_dex": str(attrs["DEX"]),
        "tf_pa_con": str(attrs["CON"]),
        "tf_pa_wil": str(attrs["WIL"]),
        "tf_pa_int": str(attrs["INT"]),
        "tf_pa_cha": str(attrs["CHA"]),
        "tf_personality_background": str(extract_background_title(bg["background"])) if bg is not None else "",
        "tf_personality_earn-place": str(ep["earn_place"]) if ep is not None else "",
        "tf_personality_life-changing-event": str(le["life_event"]) if le is not None else "",
        "tf_personality_drive": str(drive_name or ""),
        "tf_talents-1": str(chosen_talent or ""),
        "tf_nervous-tic": str(tic["tic"]) if tic is not None else "",
        "tf_drake-coins": str(coin["coins"]) if coin is not None else "",
    }

    # Add skills
    fields.update({
        f"tf_talent_{key.lower().replace(' ', '-')}": str(skill_with_bonus(skill, val))
        for skill, val in skills.items()
    })

    # Add mannerisms
    for cat, val in mannerism_options.items():
        if "confident" in cat.lower():
            fields["tf_traits_confident"] = str(val)
        elif "shy" in cat.lower():
            fields["tf_traits_shy"] = str(val)
        elif "bored" in cat.lower():
            fields["tf_traits_bored"] = str(val)
        elif "happy" in cat.lower():
            fields["tf_traits_happy"] = str(val)
        elif "frustrated" in cat.lower():
            fields["tf_traits_frustrated"] = str(val)

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
