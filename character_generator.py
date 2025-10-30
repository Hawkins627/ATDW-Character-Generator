import streamlit as st
import pandas as pd
import random
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO

# ---------- CONFIG ----------
st.set_page_config(page_title="Across a Thousand Dead Worlds – Character Creator", layout="wide")

# ---------- HELPER FUNCTIONS ----------
def load_csv(name):
    try:
        return pd.read_csv(name)
    except FileNotFoundError:
        st.warning(f"⚠️ Missing file: {name}")
        return pd.DataFrame()

def random_row(df):
    if len(df) == 0:
        return None
    return df.sample(1).iloc[0]

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
st.caption("Attributes are the foundation of every Diver and only change under specific circumstances. All characters start at 8 in each attribute and distribute 12 additional points (max 18).")

attribute_info = {
    "STR": "Strength (STR): Determines how strong your character is—how capably they perform feats of strength such as lifting heavy objects or breaking things.",
    "DEX": "Dexterity (DEX): Describes how nimble your character is—how good they are at dodging, jumping, using lockpicks and otherwise using their hands.",
    "CON": "Constitution (CON): Measures how physically resilient your character is, including how well they fare against harmful effects such as poisons or diseases.",
    "WIL": "Will (WIL): Defines mental strength and ego, including your character’s ability to stand their ground and pull themselves together after suffering a knockdown during combat.",
    "INT": "Intelligence (INT): Shows how cunning and capable your character is at mental tasks such as solving puzzles or riddles, or thinking things through before acting.",
    "CHA": "Charisma (CHA): Tells how likable your character is—how easily they can get information and gain advantages with NPCs."
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

# ---------- SKILLS ----------
st.subheader("Skills (Rulebook Pages 6–7)")
st.caption("Distribute 70 points among the following skills (no more than 10 on one skill). Skills represent prowess in a determined field. Roll a D20 + skill value to test; a 20 or higher succeeds.")

skills_info = {
    "Àrsaidh Technology": "Somewhat utilize or partially comprehend a piece of Àrsaidh technology. Required for hacking any Àrsaidh system. Due to Àrsaidh systems’ arcane nature, this skill begins at -5.",
    "Close Combat": "Fight using close-range tactics with a variety of melee weapons such as knives, clubs or even a wrench.",
    "Manipulation": "Talk to an NPC (this is typically more beneficial than shooting at them). Sometimes a silver tongue or well-placed threat is the only way to close a deal.",
    "Medical Aid": "Tie a tourniquet or stitch up a wound. This will save your life more than once. Outside of combat, remove 1 Wound from a character (advances Time Track by 1 and consumes 1 Medical Supply).",
    "Perception": "Find or be aware of things around you. It doesn’t matter how many Àrsaidh crystals you’re hauling back if you don’t notice the twisted abomination lurking behind you.",
    "Pilot": "Pilot any kind of spaceship or vehicle. Most characters aren’t pilots, but you never know when it might come in handy.",
    "Ranged Combat": "Fight using ranged weapons such as guns, pistols, rifles and anything in between.",
    "Resolve": "Withstand the psychological impact of exposure to the void’s horrors. Each time a character would gain Stress, they may roll Resolve to reduce it to 1.",
    "Science": "Recall and implement knowledge of the hard sciences. Whether it’s Biology or Physics, determines how knowledgeable a character is in these areas.",
    "Stealth": "Avoid detection and perform actions while remaining unseen. Essential for infiltration or evasion.",
    "Survival": "Orient yourself or stay alive in a hazardous environment. Most Àrsaidh environments are passable without a pressure suit, but not suited for human life.",
    "Technology": "Use technological devices (computers, electronics, comms) or patch up a system."
}

skills = {}
total_skill_points = 0
skill_cols = st.columns(3)

for i, (skill, desc) in enumerate(skills_info.items()):
    with skill_cols[i % 3]:
        if skill == "Àrsaidh Technology":
            val = st.slider(skill, -5, 10, -5, key=f"skill_{skill}", help=desc)
        else:
            val = st.slider(skill, 0, 10, 0, key=f"skill_{skill}", help=desc)
        skills[skill] = val
        # Negative starting point does not count against the total
        total_skill_points += max(val, 0)

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

# ---------- PDF GENERATION ----------
st.header("Step 5: Generate Character Sheet")

if st.button("📜 Generate Character Sheet"):
    bg = random_row(backgrounds)
    le = random_row(life_events)
    ep = random_row(earn_place)
    tic = random_row(tics)
    coin = random_row(coins)

    fields = {
        "tf_name": name,
        "tf_pa_str": attrs["STR"],
        "tf_pa_dex": attrs["DEX"],
        "tf_pa_con": attrs["CON"],
        "tf_pa_wil": attrs["WIL"],
        "tf_pa_int": attrs["INT"],
        "tf_pa_cha": attrs["CHA"],
        "tf_personality_drive": drive_name,
        "tf_talents-1": chosen_talent,
        "tf_personality_background": bg["background"] if bg is not None else "",
        "tf_personality_life-changing-event": le["life_event"] if le is not None else "",
        "tf_personality_earn-place": ep["earn_place"] if ep is not None else "",
        "tf_nervous-tic": tic["tic"] if tic is not None else "",
        "tf_drake-coins": coin["coins"] if coin is not None else "",
    }

    for cat, val in mannerism_options.items():
        if "confident" in cat.lower():
            fields["tf_traits_confident"] = val
        elif "shy" in cat.lower():
            fields["tf_traits_shy"] = val
        elif "bored" in cat.lower():
            fields["tf_traits_bored"] = val
        elif "happy" in cat.lower():
            fields["tf_traits_happy"] = val
        elif "frustrated" in cat.lower():
            fields["tf_traits_frustrated"] = val

    output = BytesIO()
    reader = PdfReader("Blank Character Sheet with fields.pdf")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.update_page_form_field_values(writer.pages[0], fields)
    writer.write(output)
    output.seek(0)

    st.download_button(
        label="⬇️ Download Character Sheet",
        data=output,
        file_name=f"{name or 'Character'}_Sheet.pdf",
        mime="application/pdf"
    )


