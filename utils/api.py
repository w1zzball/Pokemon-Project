import requests as req

API_URL = "https://pokeapi.co/api/v2/pokemon/"
fallback_img = "data/pokeball.png"


def fetch_pokemon_data(pokemon_name):
    response = req.get(f"{API_URL}{pokemon_name.lower()}")
    if response.status_code == 200:
        return response.json()
    else:
        # st.error("Failed to fetch data from PokéAPI.")
        return None


def fetch_front_sprite(pokemon_name):
    data = fetch_pokemon_data(pokemon_name)
    if data:
        return data["sprites"]["front_default"]
    else:
        return fallback_img


def fetch_back_sprite(pokemon_name):
    data = fetch_pokemon_data(pokemon_name)
    if data:
        return data["sprites"]["back_default"]
    else:
        return fallback_img
        
    
def fetch_pokemon_moves(pokemon_name):
    # Fetch full Pokemon data from the API
    data = fetch_pokemon_data(pokemon_name)
    if not data:
        return []
    # Fetch the moves the Pokemon can have 
    moves = []
    for m in data["moves"]:
        move_name = m["move"]["name"]
        moves.append(move_name)

    return moves


def fetch_move_data(move_name):
    # Get the move data from the API
    response = req.get(f"https://pokeapi.co/api/v2/move/{move_name.lower()}")
    if response.status_code == 200:
        return response.json()
    return None


def fetch_move_contest_type(move_json):
    # Get the contest type of the move
    contest_type_info = move_json.get("contest_type")
    if contest_type_info:
        return contest_type_info["name"]
    return None


def fetch_move_contest_effect(move_json):
    # Get the contest effect (appeal and jam) of the move
    contest_effect_info = move_json.get("contest_effect")
    if contest_effect_info:
        effect_url = contest_effect_info.get("url")
        effect_response = req.get(effect_url)

        if effect_response.status_code == 200:
            effect_json = effect_response.json()
            appeal = effect_json.get("appeal")
            jam = effect_json.get("jam")
            return appeal, jam

    return None, None


def fetch_move_contest_combos(move_json):
    # Get the contest combos of the move
    combos = {"use_after": [], "use_before": []}

    combo_info = move_json.get("contest_combos")
    if combo_info:
        normal_combo = combo_info.get("normal", {})

        after_moves = normal_combo.get("use_after") or []
        for move in after_moves:
            combos["use_after"].append(move["name"])

        before_moves = normal_combo.get("use_before") or []
        for move in before_moves:
            combos["use_before"].append(move["name"])

    return combos


def fetch_move_contest_data(move_name):
    # Fetch contest data for a move
    move_json = fetch_move_data(move_name)
    if not move_json:
        return None

    contest_type = fetch_move_contest_type(move_json)
    appeal, jam = fetch_move_contest_effect(move_json)
    combos = fetch_move_contest_combos(move_json)

    return {
        "move_name": move_name,
        "contest_type": contest_type,
        "appeal": appeal,
        "jam": jam,
        "combos": combos
    }


def fetch_pokemon_contest_moves(pokemon_name):
    # Get all contest moves for a given Pokemon
    moves = fetch_pokemon_moves(pokemon_name)
    contest_moves = []

    for move in moves:
        move_info = fetch_move_contest_data(move)
        if move_info and move_info["contest_type"] is not None:
            contest_moves.append(move_info)

    return contest_moves


def filter_contest_moves_by_type(contest_moves, contest_type):
    # Filter contest moves by contest type
    filtered = []

    for move in contest_moves:
        if move["contest_type"] == contest_type:
            filtered.append(move)

    return filtered


if __name__ == "__main__":
    pokemon_data = fetch_pokemon_data("Pikachu")
    if pokemon_data:
        print(pokemon_data["sprites"]["front_default"])
