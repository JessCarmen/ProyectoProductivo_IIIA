import os

import pytest
import requests


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://pproyecto-productivo-iiia-api.onrender.com",
).rstrip("/")


@pytest.mark.integration
def test_score_output_integrity():

    response = requests.get(
        f"{API_BASE_URL}/portfolio/summary",
        timeout=90,
    )

    assert response.status_code == 200

    data = response.json()

    # --------------------------------------------------------
    # Cantidad de cartera
    # --------------------------------------------------------

    assert data["total"] == 33377

    # --------------------------------------------------------
    # Clasificacion binaria
    # --------------------------------------------------------

    assert data["prediction_0"] == 21073
    assert data["prediction_1"] == 12304

    assert (
        data["prediction_0"]
        + data["prediction_1"]
        == data["total"]
    )

    # --------------------------------------------------------
    # Niveles de riesgo
    # --------------------------------------------------------

    assert data["bajo"] == 15043
    assert data["medio"] == 6328
    assert data["alto"] == 3453
    assert data["critico"] == 8553

    assert (
        data["bajo"]
        + data["medio"]
        + data["alto"]
        + data["critico"]
        == data["total"]
    )

    # --------------------------------------------------------
    # Probabilidades
    # --------------------------------------------------------

    assert 0 <= float(data["pd_min"]) <= 1
    assert 0 <= float(data["pd_promedio"]) <= 1
    assert 0 <= float(data["pd_max"]) <= 1

    assert round(
        float(data["pd_promedio"]),
        6,
    ) == round(
        0.3841617924019534,
        6,
    )

    # --------------------------------------------------------
    # Version
    # --------------------------------------------------------

    assert (
        data["model_version"]
        == "v20260929_064028"
    )
