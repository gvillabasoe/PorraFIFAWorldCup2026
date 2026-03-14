"""Core utilities for the Peñita FIFA World Cup 2026 dashboard.

This module does three things:
1. Generates a realistic sample CSV with the exact expected schema.
2. Loads any CSV that follows that schema.
3. Normalizes the wide source into report-friendly tables, including a Power BI model.
"""
from __future__ import annotations

import io
import math
import random
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

GROUP_COLORS: Dict[str, str] = {
    "A": "#62D84E",
    "B": "#FF3B30",
    "C": "#FFD60A",
    "D": "#3A86FF",
    "E": "#FF9F1C",
    "F": "#2EC4B6",
    "G": "#8338EC",
    "H": "#4CC9F0",
    "I": "#4361EE",
    "J": "#F15BB5",
    "K": "#FF006E",
    "L": "#8AC926",
}

GROUPS: Dict[str, List[str]] = {
    "A": ["USA", "Ecuador", "Senegal", "NewZealand"],
    "B": ["Brazil", "Serbia", "Japan", "Ghana"],
    "C": ["Argentina", "Mexico", "Tunisia", "Ukraine"],
    "D": ["Spain", "Morocco", "SouthKorea", "Paraguay"],
    "E": ["France", "Denmark", "Nigeria", "Peru"],
    "F": ["England", "Croatia", "Australia", "Cameroon"],
    "G": ["Germany", "Colombia", "Algeria", "Scotland"],
    "H": ["Portugal", "Uruguay", "Canada", "Iran"],
    "I": ["Italy", "Switzerland", "CostaRica", "Qatar"],
    "J": ["Netherlands", "Belgium", "Egypt", "Jamaica"],
    "K": ["Chile", "Poland", "SaudiArabia", "IvoryCoast"],
    "L": ["Turkey", "Norway", "Venezuela", "SouthAfrica"],
}

SPECIAL_OPTIONS: Dict[str, List[str]] = {
    "MejorJugador": ["Bellingham", "Mbappe", "Vinicius", "Musiala", "Valverde", "Pedri", "Foden", "Wirtz"],
    "MejorJugadorJoven": ["Yamal", "Endrick", "Guler", "Mainoo", "Tel", "Echeverri"],
    "MejorPortero": ["Alisson", "Maignan", "DibuMartinez", "UnaiSimon", "DiogoCosta", "Livakovic"],
    "MaximoGoleador": ["Mbappe", "Haaland", "Vinicius", "Kane", "JulianAlvarez", "Osimhen", "Gakpo"],
    "MaximoAsistente": ["DeBruyne", "Bellingham", "BrunoFernandes", "Pedri", "Valverde", "Foden"],
    "MaximoGoleadorESP": ["Morata", "Yamal", "NicoWilliams", "Pedri", "Oyarzabal", "Joselu"],
    "SeleccionRevelacion": ["Canada", "Japan", "Senegal", "Morocco", "Colombia", "Venezuela", "Ecuador", "Australia"],
    "SeleccionDecepcion": ["Belgium", "Croatia", "Denmark", "Mexico", "Uruguay", "Serbia", "Poland", "Qatar"],
    "PrimerGolESP": ["Morata", "Yamal", "NicoWilliams", "Pedri", "Olmo", "Joselu"],
}

PARTICIPANTS: List[str] = [
    "Aitor", "Lucía", "Sergio", "Marta", "Dani", "Irene", "Pablo", "Noa", "Javi", "Paula",
    "Álvaro", "Nerea", "Diego", "Carla", "Hugo", "Ariadna", "Rubén", "Celia", "Marcos", "Leire",
    "Adri", "Claudia", "Víctor", "Elena", "Raúl", "Sara", "Guille", "Andrea", "Óscar", "Inés",
    "Joel", "Miriam", "Bruno", "Lidia", "Borja", "Natalia", "Álex", "Patri", "Mateo", "Jimena",
]

MATCH_PAIR_ORDER: List[Tuple[int, int]] = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
BASE_HEADERS: List[str] = [
    "Participante",
    "TOTAL_PUNTOS",
    "PUNTOS_FASE_DE_GRUPOS",
    "PUNTOS_FASE_FINAL",
    "PUNTOS_ESPECIALES",
]
SPECIAL_KEYS: List[str] = [
    "MejorJugador",
    "MejorJugadorJoven",
    "MejorPortero",
    "MaximoGoleador",
    "MaximoAsistente",
    "MaximoGoleadorESP",
    "SeleccionRevelacion",
    "SeleccionDecepcion",
    "MinutoPrimerGol",
    "PrimerGolESP",
]
PRETTY_LABELS: Dict[str, str] = {
    "MejorJugador": "Mejor Jugador",
    "MejorJugadorJoven": "Mejor Jugador Joven",
    "MejorPortero": "Mejor Portero",
    "MaximoGoleador": "Máximo Goleador",
    "MaximoAsistente": "Máximo Asistente",
    "MaximoGoleadorESP": "Máximo Goleador ESP",
    "SeleccionRevelacion": "Selección Revelación",
    "SeleccionDecepcion": "Selección Decepción",
    "MinutoPrimerGol": "Minuto Primer Gol",
    "PrimerGolESP": "Primer Gol ESP",
}

FINAL_DETAIL_MAPPING: List[Tuple[str, str]] = [
    ("Participante", "Participante"),
    ("TOTAL_PUNTOS", "Puntos Totales"),
    ("PUNTOS_FASE_DE_GRUPOS", "Puntos Fase de Grupos"),
    ("PUNTOS_FASE_FINAL", "Puntos Fase Final"),
    ("PUNTOS_ESPECIALES", "Puntos Especiales"),
    ("Campeon", "Campeón"),
    ("Subcampeon", "Subcampeón"),
    ("TercerPuesto", "Tercer Puesto"),
    ("MejorJugador", "Mejor Jugador"),
    ("MejorJugadorJoven", "Mejor Jugador Joven"),
    ("MejorPortero", "Mejor Portero"),
    ("MaximoGoleador", "Máximo Goleador"),
    ("MaximoAsistente", "Máximo Asistente"),
    ("MaximoGoleadorESP", "Máximo Goleador ESP"),
    ("SeleccionRevelacion", "Selección Revelación"),
    ("SeleccionDecepcion", "Selección Decepción"),
    ("MinutoPrimerGol", "Minuto Primer Gol"),
    ("PrimerGolESP", "Primer Gol ESP"),
]

STAGE_SPECS: List[Tuple[str, int, str]] = [
    ("EquipoR32", 32, "Dieciseisavos"),
    ("EquipoOctavos", 16, "Octavos"),
    ("EquipoCuartos", 8, "Cuartos"),
    ("EquipoSemis", 4, "Semis"),
    ("EquipoFinal", 2, "Final"),
]
FINAL_SINGLETONS: List[Tuple[str, str]] = [
    ("TercerPuesto", "Tercer Puesto"),
    ("Subcampeon", "Subcampeón"),
    ("Campeon", "Campeón"),
]
SUMMARY_NUMERIC_COLUMNS: List[str] = [
    "TOTAL_PUNTOS",
    "PUNTOS_FASE_DE_GRUPOS",
    "PUNTOS_FASE_FINAL",
    "PUNTOS_ESPECIALES",
]


def pretty_team(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("_", " ")
    return re.sub(r"([a-záéíóúñ])([A-ZÁÉÍÓÚÑ])", r"\1 \2", text)


def pretty_label(value: str) -> str:
    return PRETTY_LABELS.get(value, pretty_team(value))


def hash_string(text: str) -> int:
    h = 1779033703 ^ len(text)
    for char in text:
        h = (h ^ ord(char)) * 3432918353 & 0xFFFFFFFF
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


class Mulberry32:
    def __init__(self, seed: int) -> None:
        self.seed = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.seed = (self.seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.seed
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t ^= (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0


class RNG:
    def __init__(self, seed: int) -> None:
        self._base = Mulberry32(seed)

    def random(self) -> float:
        return self._base.random()

    def randint(self, start: int, end_inclusive: int) -> int:
        return start + int(self.random() * ((end_inclusive - start) + 1))

    def choice(self, options: Sequence[Any]) -> Any:
        return options[int(self.random() * len(options))]

    def shuffle(self, items: Sequence[Any]) -> List[Any]:
        values = list(items)
        for idx in range(len(values) - 1, 0, -1):
            other = int(self.random() * (idx + 1))
            values[idx], values[other] = values[other], values[idx]
        return values


def sample_points(rng: RNG, skill: float, profile: str) -> Union[int, str]:
    roll = rng.random()
    if profile == "match":
        if roll < 0.34 - skill * 0.12:
            return 0
        if roll < 0.72 - skill * 0.06:
            return 1
        if roll < 0.92 + skill * 0.05:
            return 2
        return 3
    if profile == "group_pos":
        if roll < 0.42 - skill * 0.10:
            return 0
        if roll < 0.83:
            return 1
        return 2
    if profile == "r32":
        if roll < 0.48 - skill * 0.12:
            return 0
        if roll < 0.85:
            return 1
        return 2
    if profile == "octavos":
        if roll < 0.50 - skill * 0.10:
            return 0
        if roll < 0.86:
            return 2
        return 3
    if profile == "special_short":
        if roll < 0.55 - skill * 0.08:
            return 0
        if roll < 0.90:
            return 1
        return 2
    if profile == "special_minute":
        if roll < 0.50 - skill * 0.08:
            return 0
        if roll < 0.86:
            return 2
        return 3
    return 0


def score_pick(rng: RNG) -> str:
    return rng.choice(["0-0", "1-0", "2-1", "1-1", "2-0", "0-1", "1-2", "3-1", "2-2", "3-0", "0-2", "2-3"])


def derive_1x2(score: str) -> str:
    home, away = [int(part) for part in score.split("-")]
    if home > away:
        return "1"
    if away > home:
        return "2"
    return "X"


def sample_header_order() -> List[str]:
    headers = list(BASE_HEADERS)
    for letter, teams in GROUPS.items():
        for a, b in MATCH_PAIR_ORDER:
            prefix = f"{teams[a]}{teams[b]}"
            headers.extend([f"{prefix}_RTO", f"{prefix}_1X2", f"{prefix}_DOB", f"{prefix}_PTOS"])
        for team in teams:
            headers.extend([f"g{letter}_{team}_POS", f"g{letter}_{team}_PTOS"])
    for prefix, count, _label in STAGE_SPECS:
        for index in range(1, count + 1):
            headers.extend([f"{prefix}_{index}", f"{prefix}_{index}_PTOS"])
    headers.extend(["TercerPuesto", "TercerPuesto_PTOS", "Subcampeon", "Subcampeon_PTOS", "Campeon", "Campeon_PTOS"])
    for key in SPECIAL_KEYS:
        headers.extend([key, f"{key}_PTOS"])
    return headers


def build_sample_dataframe(participants: Optional[Sequence[str]] = None) -> pd.DataFrame:
    headers = sample_header_order()
    all_teams = [team for teams in GROUPS.values() for team in teams]
    players = list(participants) if participants is not None else list(PARTICIPANTS)
    records: List[Dict[str, Any]] = []

    for participant_index, participant_name in enumerate(players):
        rng = RNG(hash_string(participant_name) + participant_index * 97 + 2026)
        skill = min(0.92, 0.28 + ((len(players) - participant_index) / max(len(players), 1)) * 0.28 + rng.random() * 0.24)
        row: Dict[str, Any] = {"Participante": participant_name}
        group_total = 0
        final_total = 0
        special_total = 0

        for group_index, (letter, teams) in enumerate(GROUPS.items()):
            issue_mode = ""
            if participant_index % 13 == 0 and letter == "C":
                issue_mode = "double"
            elif participant_index % 17 == 0 and letter == "F":
                issue_mode = "none"
            elif participant_index % 19 == 0 and letter == "J":
                issue_mode = "double"
            chosen = int(rng.random() * len(MATCH_PAIR_ORDER))
            second = (chosen + 2) % len(MATCH_PAIR_ORDER)

            for match_index, (a, b) in enumerate(MATCH_PAIR_ORDER):
                prefix = f"{teams[a]}{teams[b]}"
                rto = score_pick(rng)
                if issue_mode == "double":
                    is_dob = match_index in (chosen, second)
                elif issue_mode == "none":
                    is_dob = False
                else:
                    is_dob = match_index == chosen
                ptos = int(sample_points(rng, skill + (group_index / 60.0), "match"))
                if is_dob and ptos > 0:
                    ptos += 2
                row[f"{prefix}_RTO"] = rto
                row[f"{prefix}_1X2"] = derive_1x2(rto)
                row[f"{prefix}_DOB"] = "TRUE" if is_dob else ""
                row[f"{prefix}_PTOS"] = ptos
                group_total += ptos

            positions = rng.shuffle([1, 2, 3, 4])
            for team_index, team in enumerate(teams):
                ptos = int(sample_points(rng, skill, "group_pos"))
                row[f"g{letter}_{team}_POS"] = positions[team_index]
                row[f"g{letter}_{team}_PTOS"] = ptos
                group_total += ptos

        for team_index, team in enumerate(rng.shuffle(all_teams)[:32], start=1):
            ptos = int(sample_points(rng, skill, "r32"))
            row[f"EquipoR32_{team_index}"] = team
            row[f"EquipoR32_{team_index}_PTOS"] = ptos
            final_total += ptos

        for team_index, team in enumerate(rng.shuffle(all_teams)[:16], start=1):
            resolved = team_index <= 8
            ptos = int(sample_points(rng, skill, "octavos")) if resolved else ""
            row[f"EquipoOctavos_{team_index}"] = team
            row[f"EquipoOctavos_{team_index}_PTOS"] = ptos
            final_total += int(ptos or 0)

        for prefix, count in [("EquipoCuartos", 8), ("EquipoSemis", 4), ("EquipoFinal", 2)]:
            for team_index, team in enumerate(rng.shuffle(all_teams)[:count], start=1):
                row[f"{prefix}_{team_index}"] = team
                row[f"{prefix}_{team_index}_PTOS"] = ""

        podium_teams = rng.shuffle(all_teams)[:3]
        row["TercerPuesto"] = podium_teams[2]
        row["TercerPuesto_PTOS"] = ""
        row["Subcampeon"] = podium_teams[1]
        row["Subcampeon_PTOS"] = ""
        row["Campeon"] = podium_teams[0]
        row["Campeon_PTOS"] = ""

        row["MejorJugador"] = rng.choice(SPECIAL_OPTIONS["MejorJugador"])
        row["MejorJugador_PTOS"] = ""
        row["MejorJugadorJoven"] = rng.choice(SPECIAL_OPTIONS["MejorJugadorJoven"])
        row["MejorJugadorJoven_PTOS"] = ""
        row["MejorPortero"] = rng.choice(SPECIAL_OPTIONS["MejorPortero"])
        row["MejorPortero_PTOS"] = ""
        row["MaximoGoleador"] = rng.choice(SPECIAL_OPTIONS["MaximoGoleador"])
        row["MaximoGoleador_PTOS"] = ""
        row["MaximoAsistente"] = rng.choice(SPECIAL_OPTIONS["MaximoAsistente"])
        row["MaximoAsistente_PTOS"] = ""
        row["MaximoGoleadorESP"] = rng.choice(SPECIAL_OPTIONS["MaximoGoleadorESP"])
        row["MaximoGoleadorESP_PTOS"] = ""
        row["SeleccionRevelacion"] = rng.choice(SPECIAL_OPTIONS["SeleccionRevelacion"])
        row["SeleccionRevelacion_PTOS"] = ""
        row["SeleccionDecepcion"] = rng.choice(SPECIAL_OPTIONS["SeleccionDecepcion"])
        row["SeleccionDecepcion_PTOS"] = ""
        row["MinutoPrimerGol"] = str(2 + int(rng.random() * 23))
        row["MinutoPrimerGol_PTOS"] = int(sample_points(rng, skill, "special_minute"))
        special_total += int(row["MinutoPrimerGol_PTOS"] or 0)
        row["PrimerGolESP"] = rng.choice(SPECIAL_OPTIONS["PrimerGolESP"])
        row["PrimerGolESP_PTOS"] = int(sample_points(rng, skill, "special_short"))
        special_total += int(row["PrimerGolESP_PTOS"] or 0)

        row["PUNTOS_FASE_DE_GRUPOS"] = group_total
        row["PUNTOS_FASE_FINAL"] = final_total
        row["PUNTOS_ESPECIALES"] = special_total
        row["TOTAL_PUNTOS"] = group_total + final_total + special_total
        records.append({header: row.get(header, "") for header in headers})

    return pd.DataFrame(records, columns=headers)


def build_sample_csv_text(participants: Optional[Sequence[str]] = None) -> str:
    df = build_sample_dataframe(participants=participants)
    return df.to_csv(index=False)


def write_sample_csv(path: Union[str, Path], participants: Optional[Sequence[str]] = None) -> Path:
    path = Path(path)
    path.write_text(build_sample_csv_text(participants=participants), encoding="utf-8-sig")
    return path


def detect_delimiter(text: str) -> str:
    first_line = next((line for line in text.replace("\ufeff", "").splitlines() if line.strip()), "")
    commas = first_line.count(",")
    semicolons = first_line.count(";")
    return ";" if semicolons > commas else ","


def load_wide_csv(source: Union[str, Path, io.StringIO, io.BytesIO]) -> pd.DataFrame:
    if isinstance(source, Path) or (isinstance(source, str) and "\n" not in source and Path(source).exists()):
        path = Path(source)
        text = path.read_text(encoding="utf-8-sig")
    elif isinstance(source, io.BytesIO):
        text = source.getvalue().decode("utf-8-sig")
    elif isinstance(source, io.StringIO):
        text = source.getvalue()
    else:
        text = str(source)

    delimiter = detect_delimiter(text)
    frame = pd.read_csv(io.StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
    frame.columns = [str(col).strip() for col in frame.columns]
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value: str(value).strip() if value is not None else "")
    return frame


def to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9,.-]", "", text).replace(",", ".")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return number


def to_int(value: Any, default: int = 0) -> int:
    number = to_number(value)
    return default if number is None else int(round(number))


def to_bool(value: Any) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "VERDADERO", "1", "SI", "SÍ", "YES", "X"}


def build_meta(columns: Iterable[str]) -> Dict[str, Any]:
    headers = list(columns)
    groups: Dict[str, Dict[str, Any]] = {}
    for header in headers:
        match = re.match(r"^g([A-L])_(.+)_(POS|PTOS)$", header)
        if match:
            letter = match.group(1)
            team = match.group(2)
            groups.setdefault(letter, {"letter": letter, "teams": [], "matches": []})
            if team not in groups[letter]["teams"]:
                groups[letter]["teams"].append(team)

    for header in headers:
        if not header.endswith("_RTO"):
            continue
        prefix = header[:-4]
        assigned_group = None
        for letter, payload in groups.items():
            teams = payload["teams"]
            for left_idx in range(len(teams)):
                for right_idx in range(left_idx + 1, len(teams)):
                    if prefix in {f"{teams[left_idx]}{teams[right_idx]}", f"{teams[right_idx]}{teams[left_idx]}"}:
                        assigned_group = letter
                        break
                if assigned_group:
                    break
            if assigned_group:
                break
        if assigned_group and prefix not in groups[assigned_group]["matches"]:
            groups[assigned_group]["matches"].append(prefix)

    detail_ptos_headers = [
        header
        for header in headers
        if header.endswith("_PTOS") and header not in {"TOTAL_PUNTOS", "PUNTOS_FASE_DE_GRUPOS", "PUNTOS_FASE_FINAL", "PUNTOS_ESPECIALES"}
    ]
    return {"headers": headers, "groups": groups, "detail_ptos_headers": detail_ptos_headers}


def find_match_teams(prefix: str, teams: Sequence[str]) -> Tuple[str, str]:
    for left_idx in range(len(teams)):
        for right_idx in range(left_idx + 1, len(teams)):
            if prefix == f"{teams[left_idx]}{teams[right_idx]}":
                return teams[left_idx], teams[right_idx]
            if prefix == f"{teams[right_idx]}{teams[left_idx]}":
                return teams[right_idx], teams[left_idx]
    return prefix, ""


def _safe_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int)


def build_powerbi_tables(wide_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    wide = wide_df.copy()
    meta = build_meta(wide.columns)

    matches_rows: List[Dict[str, Any]] = []
    positions_rows: List[Dict[str, Any]] = []
    knockout_rows: List[Dict[str, Any]] = []
    specials_rows: List[Dict[str, Any]] = []
    dob_rows: List[Dict[str, Any]] = []
    group_summary_rows: List[Dict[str, Any]] = []
    ranking_rows: List[Dict[str, Any]] = []

    for _, row in wide.iterrows():
        participant = row.get("Participante", "") or "Sin nombre"
        total = to_int(row.get("TOTAL_PUNTOS"))
        groups_total = to_int(row.get("PUNTOS_FASE_DE_GRUPOS"))
        final_total = to_int(row.get("PUNTOS_FASE_FINAL"))
        specials_total = to_int(row.get("PUNTOS_ESPECIALES"))

        hits = 0
        fails = 0
        pending = 0
        dob_ganados_total = 0
        dob_warnings = 0

        for header in meta["detail_ptos_headers"]:
            value = to_number(row.get(header))
            if value is None:
                pending += 1
            elif value > 0:
                hits += 1
            else:
                fails += 1

        for letter, payload in meta["groups"].items():
            teams = payload["teams"]
            match_prefixes = payload["matches"]
            group_points = 0
            group_hits = 0
            group_fails = 0
            group_pending = 0
            dob_count = 0
            dob_ganados_grupo = 0

            for match_prefix in match_prefixes:
                team_a, team_b = find_match_teams(match_prefix, teams)
                ptos = to_number(row.get(f"{match_prefix}_PTOS"))
                dob = to_bool(row.get(f"{match_prefix}_DOB"))
                estado = "Pendiente" if ptos is None else "Acertado" if ptos > 0 else "Fallado"
                matches_rows.append({
                    "Participante": participant,
                    "Grupo": letter,
                    "ColorGrupo": GROUP_COLORS.get(letter, ""),
                    "PartidoKey": match_prefix,
                    "EquipoA": team_a,
                    "EquipoB": team_b,
                    "Partido": f"{pretty_team(team_a)} vs {pretty_team(team_b)}",
                    "RTO": row.get(f"{match_prefix}_RTO", ""),
                    "UNO_X_DOS": row.get(f"{match_prefix}_1X2", ""),
                    "DOB": dob,
                    "PTOS": ptos,
                    "Estado": estado,
                })
                if dob:
                    dob_count += 1
                if dob and (ptos or 0) > 0:
                    dob_ganados_grupo += 1
                if ptos is None:
                    group_pending += 1
                elif ptos > 0:
                    group_hits += 1
                    group_points += int(ptos)
                else:
                    group_fails += 1

            for team in teams:
                pos = row.get(f"g{letter}_{team}_POS", "")
                ptos = to_number(row.get(f"g{letter}_{team}_PTOS"))
                estado = "Pendiente" if ptos is None else "Acertado" if ptos > 0 else "Fallado"
                positions_rows.append({
                    "Participante": participant,
                    "Grupo": letter,
                    "ColorGrupo": GROUP_COLORS.get(letter, ""),
                    "Equipo": team,
                    "EquipoBonito": pretty_team(team),
                    "Posicion": to_number(pos),
                    "PTOS": ptos,
                    "Estado": estado,
                })
                if ptos is None:
                    group_pending += 1
                elif ptos > 0:
                    group_hits += 1
                    group_points += int(ptos)
                else:
                    group_fails += 1

            dob_valido = dob_count == 1
            warning = "DOB OK" if dob_valido else ("Sin DOB" if dob_count == 0 else f"{dob_count} DOB")
            if not dob_valido:
                dob_warnings += 1
            dob_ganados_total += dob_ganados_grupo
            dob_rows.append({
                "Participante": participant,
                "Grupo": letter,
                "ColorGrupo": GROUP_COLORS.get(letter, ""),
                "DOB_Cantidad": dob_count,
                "DOB_Valido": dob_valido,
                "DOB_Warning": warning,
                "DOB_Ganados_Grupo": dob_ganados_grupo,
            })
            group_summary_rows.append({
                "Participante": participant,
                "Grupo": letter,
                "ColorGrupo": GROUP_COLORS.get(letter, ""),
                "PuntosGrupo": group_points,
                "DOB_Cantidad": dob_count,
                "DOB_Valido": dob_valido,
                "DOB_Warning": warning,
                "DOB_Ganados_Grupo": dob_ganados_grupo,
                "Aciertos": group_hits,
                "Fallos": group_fails,
                "Pendientes": group_pending,
            })

        for prefix, count, label in STAGE_SPECS:
            for idx in range(1, count + 1):
                team = row.get(f"{prefix}_{idx}", "")
                ptos = to_number(row.get(f"{prefix}_{idx}_PTOS"))
                knockout_rows.append({
                    "Participante": participant,
                    "Fase": label,
                    "FaseKey": prefix,
                    "Slot": idx,
                    "Equipo": team,
                    "EquipoBonito": pretty_team(team),
                    "PTOS": ptos,
                    "Estado": "Pendiente" if ptos is None else "Acertado" if ptos > 0 else "Fallado",
                })

        for raw_key, label in FINAL_SINGLETONS:
            ptos = to_number(row.get(f"{raw_key}_PTOS"))
            knockout_rows.append({
                "Participante": participant,
                "Fase": label,
                "FaseKey": raw_key,
                "Slot": 1,
                "Equipo": row.get(raw_key, ""),
                "EquipoBonito": pretty_team(row.get(raw_key, "")),
                "PTOS": ptos,
                "Estado": "Pendiente" if ptos is None else "Acertado" if ptos > 0 else "Fallado",
            })

        for key in SPECIAL_KEYS:
            ptos = to_number(row.get(f"{key}_PTOS"))
            specials_rows.append({
                "Participante": participant,
                "EspecialKey": key,
                "Especial": pretty_label(key),
                "Pick": row.get(key, ""),
                "PickBonito": pretty_team(row.get(key, "")),
                "PTOS": ptos,
                "Estado": "Pendiente" if ptos is None else "Acertado" if ptos > 0 else "Fallado",
            })

        ranking_rows.append({
            "Participante": participant,
            "TOTAL_PUNTOS": total,
            "PUNTOS_FASE_DE_GRUPOS": groups_total,
            "PUNTOS_FASE_FINAL": final_total,
            "PUNTOS_ESPECIALES": specials_total,
            "DOB_GANADOS": dob_ganados_total,
            "DOB_WARNINGS": dob_warnings,
            "ACIERTOS": hits,
            "FALLOS": fails,
            "PENDIENTES": pending,
        })

    fact_ranking = pd.DataFrame(ranking_rows)
    fact_ranking = fact_ranking.sort_values(
        by=["TOTAL_PUNTOS", "PUNTOS_FASE_DE_GRUPOS", "PUNTOS_FASE_FINAL", "PUNTOS_ESPECIALES", "Participante"],
        ascending=[False, False, False, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    fact_ranking["RANKING"] = range(1, len(fact_ranking) + 1)

    leader_points = int(fact_ranking["TOTAL_PUNTOS"].max()) if not fact_ranking.empty else 0
    avg_points = float(fact_ranking["TOTAL_PUNTOS"].mean()) if not fact_ranking.empty else 0.0
    stdev_points = float(fact_ranking["TOTAL_PUNTOS"].std(ddof=0)) if len(fact_ranking) > 0 else 0.0
    count = len(fact_ranking)

    fact_ranking["VS_LIDER"] = fact_ranking["TOTAL_PUNTOS"] - leader_points
    fact_ranking["VS_MEDIA"] = fact_ranking["TOTAL_PUNTOS"] - avg_points
    if count > 1:
        fact_ranking["PERCENTIL"] = ((count - fact_ranking["RANKING"]) / (count - 1) * 100).round(0).astype(int)
    else:
        fact_ranking["PERCENTIL"] = 100

    block_metric_rows: List[Dict[str, Any]] = []
    metric_specs = [
        ("TOTAL", "TOTAL_PUNTOS"),
        ("GRUPOS", "PUNTOS_FASE_DE_GRUPOS"),
        ("FASE_FINAL", "PUNTOS_FASE_FINAL"),
        ("ESPECIALES", "PUNTOS_ESPECIALES"),
        ("DOB", "DOB_GANADOS"),
    ]

    metric_averages = {label: float(fact_ranking[column].mean()) if not fact_ranking.empty else 0.0 for label, column in metric_specs}
    metric_maxima = {label: int(fact_ranking[column].max()) if not fact_ranking.empty else 0 for label, column in metric_specs}

    over_counts: List[int] = []
    under_counts: List[int] = []
    tie_counts: List[int] = []

    for _, ranking_row in fact_ranking.iterrows():
        over = 0
        under = 0
        tie = 0
        for label, column in metric_specs:
            value = float(ranking_row[column])
            average = metric_averages[label]
            maximum = metric_maxima[label]
            delta = value - average
            if delta > 0:
                over += 1
            elif delta < 0:
                under += 1
            else:
                tie += 1
            block_metric_rows.append({
                "Participante": ranking_row["Participante"],
                "Bloque": label,
                "Valor": value,
                "MediaBloque": average,
                "MaximoBloque": maximum,
                "DeltaVsMedia": delta,
                "SobreMedia": delta > 0,
                "BajoMedia": delta < 0,
                "EmpataMedia": delta == 0,
            })
        over_counts.append(over)
        under_counts.append(under)
        tie_counts.append(tie)

    fact_ranking["BLOQUES_SOBRE_MEDIA"] = over_counts
    fact_ranking["BLOQUES_BAJO_MEDIA"] = under_counts
    fact_ranking["BLOQUES_IGUAL_MEDIA"] = tie_counts

    group_matches = pd.DataFrame(matches_rows)
    group_positions = pd.DataFrame(positions_rows)
    knockout_picks = pd.DataFrame(knockout_rows)
    special_picks = pd.DataFrame(specials_rows)
    dob_validation = pd.DataFrame(dob_rows)
    group_summary = pd.DataFrame(group_summary_rows)
    participant_block_metrics = pd.DataFrame(block_metric_rows)

    dim_participantes = pd.DataFrame({"Participante": sorted(fact_ranking["Participante"].unique().tolist())})
    dim_grupos = pd.DataFrame({
        "Grupo": list(GROUP_COLORS.keys()),
        "ColorGrupo": [GROUP_COLORS[key] for key in GROUP_COLORS.keys()],
    })
    dim_especiales = pd.DataFrame({
        "EspecialKey": SPECIAL_KEYS,
        "Especial": [pretty_label(key) for key in SPECIAL_KEYS],
    })

    if not fact_ranking.empty:
        podium = fact_ranking[["Participante", "TOTAL_PUNTOS"]].head(3).copy()
        podium["PuestoPodio"] = [1, 2, 3][: len(podium)]
    else:
        podium = pd.DataFrame(columns=["Participante", "TOTAL_PUNTOS", "PuestoPodio"])

    kpi_summary = pd.DataFrame([
        {
            "Participantes": count,
            "BOTE_TOTAL": count * 20,
            "LIDER_ACTUAL": fact_ranking.iloc[0]["Participante"] if count else "",
            "LIDER_PUNTOS": int(fact_ranking.iloc[0]["TOTAL_PUNTOS"]) if count else 0,
            "MEDIA_PUNTOS": avg_points,
            "DISPERSION": stdev_points,
            "PODIO_1": fact_ranking.iloc[0]["Participante"] if count >= 1 else "",
            "PODIO_2": fact_ranking.iloc[1]["Participante"] if count >= 2 else "",
            "PODIO_3": fact_ranking.iloc[2]["Participante"] if count >= 3 else "",
        }
    ])

    final_detail = wide[[source for source, _target in FINAL_DETAIL_MAPPING]].copy()
    final_detail.columns = [target for _source, target in FINAL_DETAIL_MAPPING]

    return {
        "raw_wide": wide,
        "dim_participantes": dim_participantes,
        "dim_grupos": dim_grupos,
        "dim_especiales": dim_especiales,
        "fact_ranking": fact_ranking,
        "fact_group_matches": group_matches,
        "fact_group_positions": group_positions,
        "fact_knockout_picks": knockout_picks,
        "fact_special_picks": special_picks,
        "fact_dob_validation": dob_validation,
        "fact_group_summary": group_summary,
        "fact_block_metrics": participant_block_metrics,
        "fact_podio": podium,
        "kpi_summary": kpi_summary,
        "final_detail": final_detail,
    }


def export_powerbi_tables(tables: Dict[str, pd.DataFrame], out_dir: Union[str, Path]) -> Dict[str, Path]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    exported: Dict[str, Path] = {}
    for name, frame in tables.items():
        file_path = out_path / f"{name}.csv"
        frame.to_csv(file_path, index=False, encoding="utf-8-sig")
        exported[name] = file_path
    return exported


def load_or_sample(source: Optional[Union[str, Path, io.StringIO, io.BytesIO]] = None) -> pd.DataFrame:
    if source is None:
        return build_sample_dataframe()
    return load_wide_csv(source)


def get_selected_participant_snapshot(tables: Dict[str, pd.DataFrame], participant: str) -> Dict[str, pd.DataFrame]:
    return {
        name: frame[frame["Participante"] == participant].copy()
        for name, frame in tables.items()
        if isinstance(frame, pd.DataFrame) and "Participante" in frame.columns
    }


__all__ = [
    "GROUP_COLORS",
    "GROUPS",
    "PARTICIPANTS",
    "PRETTY_LABELS",
    "SPECIAL_KEYS",
    "SPECIAL_OPTIONS",
    "FINAL_DETAIL_MAPPING",
    "build_sample_csv_text",
    "build_sample_dataframe",
    "build_powerbi_tables",
    "detect_delimiter",
    "export_powerbi_tables",
    "get_selected_participant_snapshot",
    "load_or_sample",
    "load_wide_csv",
    "pretty_label",
    "pretty_team",
    "write_sample_csv",
]
