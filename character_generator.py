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
sget("bg_bonus_opts", None)  # tuple (opt1, opt2)
sget("bg_bonus_choice", None)  # string of the chosen skill
sget("bg_bonus_applied", False)  # True if user applied the +1 bonus

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
    """Parse 'Choose: +1 X or +1 Y' from background text."""
    if not isinstance(text, str):
        return None
    m = re.search(r"Choose:\s*\+1\s*(.*?)\s*or\s*\+1\s*(.*?)(?:\.|$)", text)
    if not m:
        return None
    return (m.group(1).strip(), m.group(2).strip())

def add_need_appearances(writer: PdfWriter):
    """Ensure PDF form values are visible in all viewers."""
    try:
        catalog = writer._root_object
        if "/AcroForm" not in catalog:
            catalog[NameObject("/AcroForm")] = writer._add_object(DictionaryObject())
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    except Exception as e:
        print("⚠️ Could not set NeedAppearances:", e)

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
st.caption("All characters start at 8 in each attribute and distribute 12 additional points (max 18).")

attribute_info = {
    "STR": "Strength – lifting, breaking, and power.",
    "DEX": "Dexterity – agility, precision, and coordination.",
    "CON": "Constitution – endurance and toughness.",
    "WIL": "Will – mental fortitude and resolve.",
    "INT": "Intelligence – reasoning and logic.",
    "CHA": "Charisma – charm and presence."
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
with st.expander("📘 Secondary Attributes (Rulebook Page 5)"):
    st.markdown("""
**Luck:** Spend to re-roll or avoid death.  
**Stamina:** Start 10. Recharges each round.  
**Stress:** Start 0. Increases with trauma.  
**Wounds:** Max 3 before death.
""")

# ---------- SKILLS ----------
st.subheader("Skills (Rulebook Pages 6–7)")
st.caption("Distribute 70 points among the following skills (max 10 per skill).")

skills_info = {
    "Àrsaidh Technology": "Hacking or understanding Àrsaidh systems. Starts at -5.",
    "Close Combat": "Melee fighting.",
    "Manipulation": "Persuasion or intimidation.",
    "Medical Aid": "Treat wounds and injuries.",
    "Perception": "Awareness of surroundings.",
    "Pilot": "Operating vehicles or spacecraft.",
    "Ranged Combat": "Using ranged weapons.",
    "Resolve": "Mental resilience under pressure.",
    "Science": "Knowledge of the hard sciences.",
    "Stealth": "Remaining unseen.",
    "Survival": "Enduring harsh environments.",
    "Technology": "Repairing and using electronics."
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

# Background bonus UI
if st.session_state.bg_bonus_opts is not None:
    opt1, opt2 = st.session_state.bg_bonus_opts
    st.markdown(f"**Background Skill Choice:** You may add +1 to either `{opt1}` or `{opt2}` (free, does not count against 70).")
    st.session_state.bg_bonus_choice = st.radio(
        "Select your +1 Skill Bonus", [opt1, opt2],
        index=0 if st.session_state.bg_bonus_choice is None else [opt1, opt2].index(st.session_state.bg_bonus_choice)
    )
    if st.button("✅ Apply Background Bonus"):
        st.session_state.bg_bonus_applied = True
        st.success(f"Background bonus ready: +1 to **{st.session_state.bg_bonus_choice}** will be applied on the PDF output.")

# ---------- STEP 6: GENERATE PDF ----------
st.header("Step 6: Generate Character Sheet")

def skill_with_bonus(skill_name, base_value):
    """Return base_value plus background +1 if applied/selected for this skill."""
    if st.session_state.bg_bonus_applied and st.session_state.bg_bonus_choice == skill_name:
        return base_value + 1
    return base_value

def extract_background_title(text):
    """Extract only the background title (before any dash, colon, or description)."""
    if not isinstance(text, str):
        return ""
    # Common separators used in the backgrounds file
    for sep in [" - ", " — ", "–", ":", "—"]:
        if sep in text:
            return text.split(sep)[0].strip()
    # Fallback: first 5 words max, just in case
    return " ".join(text.split()[:5]).strip()

if st.button("📜 Generate Character Sheet"):
    # Ensure all rolls exist
    if st.session_state.rolled_background is None:
        st.session_state.rolled_background = random_row(backgrounds)
        st.session_state.bg_bonus_opts = parse_background_bonus(st.session_state.rolled_background["background"] if st.session_state.rolled_background is not None else "")
    if st.session_state.rolled_life_event is None:
        st.session_state.rolled_life_event = random_row(life_events)
    if st.session_state.rolled_earn_place is None:
        st.session_state.rolled_earn_place = random_row(earn_place)
    if st.session_state.rolled_tic is None:
        st.session_state.rolled_tic = random_row(tics)
    if st.session_state.rolled_coins is None:
        st.session_state.rolled_coins = random_row(coins)

    # Default to first background option if unconfirmed
    if (st.session_state.bg_bonus_opts is not None) and (not st.session_state.bg_bonus_applied):
        st.session_state.bg_bonus_choice = st.session_state.bg_bonus_opts[0]
        st.session_state.bg_bonus_applied = True

    bg = st.session_state.rolled_background
    le = st.session_state.rolled_life_event
    ep = st.session_state.rolled_earn_place
    tic = st.session_state.rolled_tic
    coin = st.session_state.rolled_coins

    # PDF fields
    fields = {
        "tf_name": str(name or ""),
        "tf_pa_str": str(attrs["STR"]),
        "tf_pa_dex": str(attrs["DEX"]),
        "tf_pa_con": str(attrs["CON"]),
        "tf_pa_wil": str(attrs["WIL"]),
        "tf_pa_int": str(attrs["INT"]),
        "tf_pa_cha": str(attrs["CHA"]),
        "tf_personality_background": "",  # Blank line for title header
        "tf_personality_earn-place": (
            extract_background_title(bg["background"]) if bg is not None else ""
        ),
        "tf_personality_life-changing-event": str(ep["earn_place"]) if ep is not None else "",
        "tf_personality_drive": str(le["life_event"]) if le is not None else "",
        "tf_personality_other-details_1": str(drive_name or ""),
        "tf_personality_other-details_2": "",
        "tf_talents-1": str(chosen_talent or ""),
        "tf_nervous-tic": str(tic["tic"]) if tic is not None else "",
        "tf_drake-coins": str(coin["coins"]) if coin is not None else "",
    }

    # Add skills
    fields.update({
        "tf_talent_arsaidh-technology": str(skill_with_bonus("Àrsaidh Technology", skills["Àrsaidh Technology"])),
        "tf_talent_close-combat": str(skill_with_bonus("Close Combat", skills["Close Combat"])),
        "tf_talent_perception": str(skill_with_bonus("Perception", skills["Perception"])),
        "tf_talent_manipulation": str(skill_with_bonus("Manipulation", skills["Manipulation"])),
        "tf_talent_medical-aid": str(skill_with_bonus("Medical Aid", skills["Medical Aid"])),
        "tf_talent_pilot": str(skill_with_bonus("Pilot", skills["Pilot"])),
        "tf_talent_ranged-combat": str(skill_with_bonus("Ranged Combat", skills["Ranged Combat"])),
        "tf_talent_resolve": str(skill_with_bonus("Resolve", skills["Resolve"])),
        "tf_talent_science": str(skill_with_bonus("Science", skills["Science"])),
        "tf_talent_stealth": str(skill_with_bonus("Stealth", skills["Stealth"])),
        "tf_talent_survival": str(skill_with_bonus("Survival", skills["Survival"])),
        "tf_talent_technology": str(skill_with_bonus("Technology", skills["Technology"])),
    })

    # --- Mannerisms ---
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

    if "/AcroForm" in reader.trailer["/Root"]:
        writer._root_object.update({
            NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
        })

    for page in writer.pages:
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

    st.success("✅ Character sheet generated successfully! Open the downloaded PDF to see all fields filled in.")



