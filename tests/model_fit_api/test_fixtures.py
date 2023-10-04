def test_flux_jansky_dif(flux_jansky_dif):
    assert len(flux_jansky_dif) == 468


def test_lc_data(lc_data):
    assert len(lc_data["light_curve"]) == 468
    assert len(lc_data) == 7
