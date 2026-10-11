import json
from pathlib import Path

from analisis.eurostat import labels, load_raw, parse_jsonstat, save_raw

FIXTURE = Path(__file__).parent / "fixtures" / "mini.json"


def test_parse_jsonstat_valores_dispersos():
    df = parse_jsonstat(json.loads(FIXTURE.read_text()))
    assert list(df.columns) == ["freq", "geo", "time", "value"]
    # La posición 4 (UE, febrero) no existe en el diccionario disperso: no aparece.
    assert len(df) == 5
    ue = df[df.geo == "EU27_2020"].set_index("time")["value"].to_dict()
    assert ue == {"2024-01": 6.0, "2024-03": 5.9}
    es = df[df.geo == "ES"].set_index("time")["value"].to_dict()
    assert es == {"2024-01": 11.6, "2024-02": 11.5, "2024-03": 11.4}


def test_parse_jsonstat_lista_con_nulos():
    data = json.loads(FIXTURE.read_text())
    data["value"] = [11.6, None, 11.4, 6.0, 6.1, 5.9]
    df = parse_jsonstat(data)
    assert len(df) == 5
    assert "2024-02" not in set(df[df.geo == "ES"].time)


def test_labels_y_guardado(tmp_path):
    data = json.loads(FIXTURE.read_text())
    assert labels(data, "geo")["ES"] == "Spain"
    assert labels(data, "time") == {}
    path = tmp_path / "sub" / "x.json"
    save_raw(data, path)
    assert load_raw(path) == data
