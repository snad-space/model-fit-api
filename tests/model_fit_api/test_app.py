from fastapi.testclient import TestClient

from src.model_fit_api.app import app


TEST_CLIENT = TestClient(app)


def test_app(lc_data):
    responce = TEST_CLIENT.post(
        "/api/v1/sncosmo",
        json=lc_data,
    )
    assert responce.status_code == 200

    data = responce.json()

    nbands_requested = len(set([obs["band"] for obs in lc_data["light_curve"]]))
    nbands_returned = len(set([point["band"] for point in data["flux_jansky"]]))
    assert nbands_requested == nbands_returned

    nobs_requested = lc_data["count"] * nbands_requested
    nobs_returned = len(data["flux_jansky"])
    assert nobs_requested == nobs_returned

    dof_expected = len(lc_data["light_curve"]) - len(data["parameters"])
    assert dof_expected == data["degrees_of_freedom"]
