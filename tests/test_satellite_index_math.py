from services.satellite.analytics.index_math import calculate_ndmi_values


def test_calculate_ndmi_values_handles_basic_case() -> None:
    nir = [0.8, 0.6, 0.0]
    swir = [0.2, 0.6, 0.0]

    result = calculate_ndmi_values(nir, swir)

    assert result[0] == 0.6
    assert result[1] == 0.0
    assert result[2] == -9999.0


def test_calculate_ndmi_values_requires_same_length() -> None:
    nir = [0.8]
    swir = [0.2, 0.1]

    try:
        calculate_ndmi_values(nir, swir)
        assert False, "Expected ValueError for different list sizes"
    except ValueError as exc:
        assert "same length" in str(exc)
