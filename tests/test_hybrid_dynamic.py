from hybrid import dynamic    # The code to test

def test_find_logcat_errors_anr_errors():

    path = "tests/data/hybrid/dynamic/0.eu.kanade.tachiyomi_41.apk.log"
    errors = dynamic.find_logcat_errors(path)

    assert errors == ["42"]

    # assert False


def test_find_logcat_errors_class_not_found_errors():

    path = "tests/data/hybrid/dynamic/1.io.github.lonamiwebs.klooni_820.apk.log"
    errors = dynamic.find_logcat_errors(path)

    assert errors == ["42"]
