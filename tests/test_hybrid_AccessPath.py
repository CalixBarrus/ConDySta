

from hybrid.AccessPath import AccessPath


def test_smoke():

    path = AccessPath("[<str .>]")

    assert True

def test_constructor_on_list():
    
    access_path = "[<org.Container .>, <java.lang.String secret>]"

    path = AccessPath(access_path)

    assert len(path.fields) == 2


def test_to_string():

    access_path = "[<org.Container .>, <java.lang.String secret>]"
    path = AccessPath(access_path)

    assert str(path) == "[<org.Container .>, <java.lang.String secret>]"

def test_usable_as_key():

    access_path = "[<org.Container .>, <java.lang.String secret>]"
    path = AccessPath(access_path)
    path2 = AccessPath(access_path)

    dictionary = dict()
    dictionary[path] = 42
    _ = dictionary[path2]
    assert True