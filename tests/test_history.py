from src.history import record_details


def _details(record):
    return dict(record_details(record))


def test_history_displays_new_answers():
    details = _details({"ate_fruit": True, "freshened_up": False})
    assert details["Fruit"] == "Yes"
    assert details["Freshened up after waking"] == "No"


def test_history_labels_legacy_nulls_as_not_tracked():
    details = _details({"ate_fruit": None, "freshened_up": None})
    assert details["Fruit"] == "Not tracked"
    assert details["Freshened up after waking"] == "Not tracked"
