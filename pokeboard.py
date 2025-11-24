import pandas as pd
import streamlit as st
import plotly.express as px
from utils.api import fetch_back_sprite, fetch_pokemon_data, fetch_front_sprite
from utils.type_utils import type_effectiveness
import plotly.graph_objects as go
import math

# TODO refactor into separate files
# import data
poke_data = pd.read_csv("data/cleaned_pokemon.csv")


# set up streamlit
st.title("PokéBoard")
# st.subheader("An interactive Pokédex data explorer")
st.set_page_config(page_title="PokéBoard")


def normalize(series):
    return (series - series.min()) / (series.max() - series.min())


for col in ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
    # add normalised columns
    poke_data[f"{col}_norm"] = normalize(poke_data[col])

normalise = False
fallback_img = "data/pokeball.png"

eng_pokemon_names = poke_data["name"].tolist()
ger_pokemon_names = poke_data["german_name"].tolist()
jpn_pokemon_names = poke_data["japanese_name"].tolist()

language_data = {
    "English": {"name_list": eng_pokemon_names, "column": "name"},
    "Deutsch": {"name_list": ger_pokemon_names, "column": "german_name"},
    "日本語": {"name_list": jpn_pokemon_names, "column": "japanese_name"},
}

type_list = poke_data["type_1"].unique().tolist()
type_list.extend(poke_data["type_2"].unique().tolist())
type_list = list(set(type_list))


stats_list = [
    "hp",
    "attack",
    "defense",
    "sp_attack",
    "sp_defense",
    "speed",
    "type_1",
    "type_2",
    "height_m",
    "weight_kg",
]

STAT_KEYS = stats_list[:-4]
NEUTRAL_MODIFIERS = {key: 1.0 for key in STAT_KEYS}
DEFAULT_NATURE = "Neutral"
NATURE_MODIFIERS = {
    "Neutral": {},
    "Hardy": {},
    "Docile": {},
    "Serious": {},
    "Bashful": {},
    "Quirky": {},
    "Lonely": {"attack": 1.1, "defense": 0.9},
    "Brave": {"attack": 1.1, "speed": 0.9},
    "Adamant": {"attack": 1.1, "sp_attack": 0.9},
    "Naughty": {"attack": 1.1, "sp_defense": 0.9},
    "Bold": {"defense": 1.1, "attack": 0.9},
    "Relaxed": {"defense": 1.1, "speed": 0.9},
    "Impish": {"defense": 1.1, "sp_attack": 0.9},
    "Lax": {"defense": 1.1, "sp_defense": 0.9},
    "Timid": {"speed": 1.1, "attack": 0.9},
    "Hasty": {"speed": 1.1, "defense": 0.9},
    "Jolly": {"speed": 1.1, "sp_attack": 0.9},
    "Naive": {"speed": 1.1, "sp_defense": 0.9},
    "Modest": {"sp_attack": 1.1, "attack": 0.9},
    "Mild": {"sp_attack": 1.1, "defense": 0.9},
    "Quiet": {"sp_attack": 1.1, "speed": 0.9},
    "Rash": {"sp_attack": 1.1, "sp_defense": 0.9},
    "Calm": {"sp_defense": 1.1, "attack": 0.9},
    "Gentle": {"sp_defense": 1.1, "defense": 0.9},
    "Sassy": {"sp_defense": 1.1, "speed": 0.9},
    "Careful": {"sp_defense": 1.1, "sp_attack": 0.9},
}
NATURE_OPTIONS = list(NATURE_MODIFIERS.keys())

# sidebar
st.sidebar.title("Settings")
normalise = st.sidebar.checkbox("Normalise stats", value=False)
# language
language = st.sidebar.selectbox(
    "Select language", ["English", "Deutsch", "日本語"], index=0
)

# Nature filter
apply_nature_filter = st.sidebar.checkbox("Apply nature filter", value=False)
if apply_nature_filter:
    selected_nature = st.sidebar.selectbox(
        "Nature",
        NATURE_OPTIONS,
        index=NATURE_OPTIONS.index(DEFAULT_NATURE),
    )
else:
    selected_nature = DEFAULT_NATURE


# plotly radar
def radar_chart(df, selected_pokemon_name, modifiers):
    pokemon = df[
        df[language_data[language]["column"]] == selected_pokemon_name
    ]
    categories = [
        f"hp{'' if not normalise else '_norm'}",
        f"attack{'' if not normalise else '_norm'}",
        f"defense{'' if not normalise else '_norm'}",
        f"sp_attack{'' if not normalise else '_norm'}",
        f"sp_defense{'' if not normalise else '_norm'}",
        f"speed{'' if not normalise else '_norm'}",
    ]
    values = []
    for cat in categories:
        base_value = pokemon[cat].iloc[0]
        base_stat = cat.replace("_norm", "")
        values.append(base_value * modifiers.get(base_stat, 1.0))

    fig = px.line_polar(
        r=values,
        theta=[
            cat.replace("_norm", "")
            .replace("sp_", "S.")
            .replace("attack", "Atk")
            .replace("defense", "Def")
            .replace("speed", "Spd")
            .replace("hp", "HP")
            for cat in categories
        ],
        line_close=True,
        color_discrete_sequence=["red"],
    )
    fig.update_layout(
        width=400,
        height=400,
        polar=dict(
            radialaxis=dict(
                visible=False,  # hide radial axis
                showline=False,
                # showticklabels=False,
                showgrid=False,
            ),
            angularaxis=dict(
                # visible=False,  # hide angular axis
                showline=False,
                # showticklabels=False,
                showgrid=False,
            ),
            bgcolor="white",  # background
        ),
        showlegend=False,
    )
    fig.update_traces(fill="toself", fillcolor="rgba(255,0,0,0.3)")
    return fig


# set default pokemon to pikachu
if st.session_state.get("first_run", True):
    st.session_state["first_run"] = False
    st.session_state["selected_pokemon_idx"] = 32

# stateful pokemon selector
stored_idx = st.session_state.get("selected_pokemon_idx", poke_data.index[0])
try:
    selectbox_pos = int(poke_data.index.get_loc(stored_idx))  # type: ignore
except Exception:
    # fallback to first position if stored index not found
    selectbox_pos = 0


selected_name = st.session_state.get("selected_pokemon_name_widget")

if selected_name is not None:
    matched = poke_data[
        poke_data[language_data[language]["column"]] == selected_name
    ]
    if not matched.empty:
        new_idx = matched.index[0]
        st.session_state["selected_pokemon_idx"] = new_idx
    else:
        # selected name not found, use old index
        new_idx = st.session_state.get(
            "selected_pokemon_idx", poke_data.index[0]
        )
else:
    new_idx = st.session_state.get("selected_pokemon_idx", poke_data.index[0])

st.session_state.selected_pokemon = poke_data.loc[[new_idx]]
selected_pokemon_index = new_idx
selected_pokemon_name = st.session_state.selected_pokemon[
    language_data[language]["column"]
].iloc[0]

modifiers = NEUTRAL_MODIFIERS.copy()
if apply_nature_filter:
    modifiers.update(NATURE_MODIFIERS.get(selected_nature, {}))

chart = radar_chart(poke_data, selected_pokemon_name, modifiers)
pokemon_api_data = fetch_pokemon_data(selected_pokemon_name)

overview, match_up, IV_calculator = st.tabs(
    ["Overview", "Match-up", "IV Calculator"]
)

with overview:
    st.selectbox(
        "Select a Pokémon",
        language_data[language]["name_list"],
        index=selectbox_pos,
        key="selected_pokemon_name_widget",
    )
    with st.container(horizontal=True, key="overview-main"):
        with st.container(key="radar"):
            st.plotly_chart(chart)
        with st.container(key="sprites-and-info"):
            with st.container(key="sprites", horizontal=True):
                front_sprite = fetch_front_sprite(
                    st.session_state.selected_pokemon[
                        language_data["English"]["column"]
                    ].iloc[0]
                )
                back_sprite = fetch_back_sprite(
                    st.session_state.selected_pokemon[
                        language_data["English"]["column"]
                    ].iloc[0]
                )
                st.image(
                    front_sprite,
                    width=150,
                    caption="Front Sprite",
                )
                st.image(
                    back_sprite,
                    width=150,
                    caption="Back Sprite",
                )
            with st.container(key="info", horizontal_alignment="center"):
                st.markdown(f"### {selected_pokemon_name} Info")
                selected = st.session_state.selected_pokemon.iloc[0]
                type1 = (
                    selected["type_1"]
                    if not pd.isna(selected["type_1"])
                    else "none"
                )
                type2 = (
                    selected["type_2"]
                    if not pd.isna(selected["type_2"])
                    else "none"
                )

                info_df = pd.DataFrame(
                    {
                        "Attribute": [
                            "Height (m)",
                            "Weight (kg)",
                            "Type 1",
                            "Type 2",
                        ],
                        "Value": [
                            selected["height_m"],
                            selected["weight_kg"],
                            type1,
                            type2,
                        ],
                    }
                )

                st.table(info_df)
                with st.container(border=True):
                    filter_text = (
                        f"Nature filter: {selected_nature}"
                        if apply_nature_filter
                        else "No filters applied"
                    )
                    st.markdown(filter_text)


with match_up:
    with st.container(key="match-up", horizontal=True):
        with st.container(key="dropdowns", horizontal=True):
            st.selectbox(
                "Select attacker",
                language_data[language]["name_list"],
                key="first_matchup_pokemon_name",
            )

            def swap_pokemon():
                first_name = st.session_state.get(
                    "first_matchup_pokemon_name", None
                )
                second_name = st.session_state.get(
                    "second_matchup_pokemon_name", None
                )
                st.session_state["first_matchup_pokemon_name"] = second_name
                st.session_state["second_matchup_pokemon_name"] = first_name

            st.button("Swap", on_click=swap_pokemon)
            st.selectbox(
                "Select defender",
                language_data[language]["name_list"],
                key="second_matchup_pokemon_name",
            )
            first_pokemon_name = st.session_state.get(
                "first_matchup_pokemon_name", None
            )
            first_pokemon = poke_data[
                poke_data[language_data[language]["column"]]
                == first_pokemon_name
            ]
            second_pokemon_name = st.session_state.get(
                "second_matchup_pokemon_name", None
            )
            second_pokemon = poke_data[
                poke_data[language_data[language]["column"]]
                == second_pokemon_name
            ]

        # when both pokemon are selected show a coloured stat comparison
    with st.container(key="stat-selector"):
        stats = [
            "hp",
            "attack",
            "defense",
            "sp_attack",
            "sp_defense",
            "speed",
        ]
        stats = st.multiselect(
            "select stats to compare", stats_list, default=stats_list
        )
    with st.container(key="stat-comparison"):
        if not first_pokemon.empty and not second_pokemon.empty:
            # TODO add images
            st.markdown(
                f"### Match-up: {first_pokemon_name} attacking {second_pokemon_name}"
            )

            header_cols = st.columns([1, 1, 1])
            header_cols[0].markdown("**Stat**")
            header_cols[1].markdown(f"**{first_pokemon_name}**")
            header_cols[2].markdown(f"**{second_pokemon_name}**")

            for stat in stats:
                stat1 = first_pokemon.iloc[0][stat]
                stat2 = second_pokemon.iloc[0][stat]

                try:
                    # attempt numeric comparison
                    num_stat1 = float(stat1)
                    num_stat2 = float(stat2)
                except Exception:
                    num_stat1 = stat1
                    num_stat2 = stat2

                if isinstance(num_stat1, (int, float)) and isinstance(
                    num_stat2, (int, float)
                ):
                    if num_stat1 > num_stat2:
                        c1, c2 = "green", "red"
                    elif num_stat1 < num_stat2:
                        c1, c2 = "red", "green"
                    else:
                        c1, c2 = "goldenrod", "goldenrod"
                elif stat in ("type_1", "type_2"):
                    stat1 = first_pokemon.iloc[0][stat]
                    stat2 = second_pokemon.iloc[0][stat]
                    stat1 = "none" if pd.isna(stat1) else stat1
                    stat2 = "none" if pd.isna(stat2) else stat2
                    if stat1 in type_list and stat2 in type_list:
                        multiplier = type_effectiveness(stat1, stat2)
                    else:
                        multiplier = 1
                    if multiplier > 1:
                        c1, c2 = "green", "red"
                    elif multiplier < 1:
                        c1, c2 = "red", "green"
                    else:
                        c1, c2 = "goldenrod", "goldenrod"
                else:
                    # fallback: equal is yellow, else black
                    if num_stat1 == num_stat2:
                        c1 = c2 = "goldenrod"
                    else:
                        c1 = c2 = "black"

                row_cols = st.columns([1, 1, 1])
                row_cols[0].markdown(f"`{stat}`")
                row_cols[1].markdown(
                    f"<span style='color:{c1}; font-weight:600'>{stat1}</span>",
                    unsafe_allow_html=True,
                )
                row_cols[2].markdown(
                    f"<span style='color:{c2}; font-weight:600'>{stat2}</span>",
                    unsafe_allow_html=True,
                )


with IV_calculator:

    def compute_stat(
        base: int,
        iv: int,
        ev: int,
        level: int,
        is_hp: bool,
        nature_multiplier: float = 1.0,
    ) -> int:
        ev_term = ev // 4
        if is_hp:
            return (
                math.floor(((2 * base + iv + ev_term) * level) / 100)
                + level
                + 10
            )
        else:
            stat_value = (
                math.floor(((2 * base + iv + ev_term) * level) / 100) + 5
            )
            # apply nature multiplier for non-HP stats
            return math.floor(stat_value * nature_multiplier)

    st.header("Pokémon IV Calculator")

    stats = [
        "hp",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
    ]

    # Map dataframe column names -> display labels
    STAT_LABELS = {
        "hp": "HP",
        "attack": "Attack",
        "defense": "Defense",
        "sp_attack": "Sp. Attack",
        "sp_defense": "Sp. Defense",
        "speed": "Speed",
    }

    st.header("Pokémon IV / EV Calculator (Radar View)")

    # ---- Inputs: Pokémon selection ----
    pokemon_name = st.selectbox("Pokémon", sorted(poke_data["name"].unique()))

    # Level slider
    level = st.slider("Level", min_value=1, max_value=100, value=50, step=1)

    # ---- Lookup row ----
    try:
        row = poke_data.loc[poke_data["name"] == pokemon_name].iloc[0]
    except IndexError:
        st.error("Selected Pokémon not found in the base stats table.")
        st.stop()

    # ---- IV & EV inputs per stat ----
    st.subheader("IV and EV Inputs (per stat)")
    st.caption(
        f"Nature filter: {selected_nature}"
        if apply_nature_filter
        else "Nature filter: Off"
    )

    iv_values = {}
    ev_values = {}
    cols_iv = st.columns(6)
    cols_ev = st.columns(6)

    # IVs
    for i, stat in enumerate(stats):
        with cols_iv[i]:
            iv_values[stat] = st.number_input(
                f"{STAT_LABELS[stat]} IV",
                min_value=0,
                max_value=31,
                value=31,
                step=1,
            )

    # EVs
    for i, stat in enumerate(stats):
        with cols_ev[i]:
            ev_values[stat] = st.number_input(
                f"{STAT_LABELS[stat]} EV",
                min_value=0,
                max_value=252,
                value=0,
                step=4,
            )

    # ---- Compute stats at the chosen level ----
    base_stats = []
    modified_stats = []
    labels = []

    for stat in stats:
        base_stat_value = int(row[stat])  # base stat from the dataset
        iv = iv_values[stat]
        ev = ev_values[stat]

        is_hp = stat == "hp"
        nature_multiplier = modifiers.get(stat, 1.0)

        # Stat with 0 IV / 0 EV (nature does not modify base comparison)
        base_val = compute_stat(
            base_stat_value,
            iv=0,
            ev=0,
            level=level,
            is_hp=is_hp,
            nature_multiplier=1.0,
        )

        # Stat with chosen IV / EV
        modified_val = compute_stat(
            base_stat_value,
            iv=iv,
            ev=ev,
            level=level,
            is_hp=is_hp,
            nature_multiplier=nature_multiplier,
        )

        base_stats.append(base_val)
        modified_stats.append(modified_val)
        labels.append(STAT_LABELS[stat])

    # Close the radar loop (first point repeated at end)
    radar_labels = labels + labels[:1]
    radar_base = base_stats + base_stats[:1]
    radar_modified = modified_stats + modified_stats[:1]

    # ---- Radar chart ----
    st.subheader("Stat Distribution (Radar Chart)")

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=radar_base,
            theta=radar_labels,
            fill="toself",
            name="Base stats (0 IV / 0 EV)",
            opacity=0.5,
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=radar_modified,
            theta=radar_labels,
            fill="toself",
            name="With IV + EV",
            opacity=0.5,
        )
    )

    fig.update_layout(
        width=400,
        height=400,
        polar=dict(
            radialaxis=dict(
                visible=False,  # hide radial axis
                showline=False,
                # showticklabels=False,
                showgrid=False,
            ),
            angularaxis=dict(
                # visible=False,  # hide angular axis
                showline=False,
                # showticklabels=False,
                showgrid=False,
            ),
            bgcolor="white",  # background
        ),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Numeric comparison table ----
    st.subheader("Numeric Comparison")
    comparison_rows = []
    for label, base, mod in zip(labels, base_stats, modified_stats):
        comparison_rows.append(
            {
                "Stat": label,
                "Base (0 IV / 0 EV)": base,
                "With IV + EV": mod,
                "Change": mod - base,
            }
        )

    st.table(comparison_rows)
