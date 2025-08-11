import pytest

from UnityPy.helpers.UnityVersion import UnityVersion, UnityVersionType


@pytest.mark.parametrize(
    "version_str, expected_tuple",
    [
        ("2018.1.1f2", (2018, 1, 1, UnityVersionType.f.value, 2)),
        ("5.0.0", (5, 0, 0, UnityVersionType.f.value, 0)),
        ("2020.3.12b1", (2020, 3, 12, UnityVersionType.b.value, 1)),
        ("2019.4.28a3", (2019, 4, 28, UnityVersionType.a.value, 3)),
        ("2017.2.0p1", (2017, 2, 0, UnityVersionType.p.value, 1)),
        ("2021.1.0c1", (2021, 1, 0, UnityVersionType.c.value, 1)),
        ("2022.2.0x1", (2022, 2, 0, UnityVersionType.x.value, 1)),
        ("2018.1.1z2", (2018, 1, 1, UnityVersionType.u.value, 2)),  # unknown type
    ],
)
def test_parse_unity_version(version_str, expected_tuple):
    v = UnityVersion.from_str(version_str)
    assert v.as_tuple() == expected_tuple
    assert v.major == expected_tuple[0]
    assert v.minor == expected_tuple[1]
    assert v.build == expected_tuple[2]
    assert v.type.value == expected_tuple[3]
    assert v.type_number == expected_tuple[4]


@pytest.mark.parametrize(
    "version_str, compare_tuple",
    [
        ("2018.1.1f2", (2018, 1, 1, UnityVersionType.f.value, 2)),
        ("2018.1.1f2", (2018, 1, 1, UnityVersionType.f.value, 1)),
        ("2018.1.1f2", (2018, 1, 2, UnityVersionType.f.value, 2)),
        ("2018.1.1f2", (2018, 2, 1, UnityVersionType.f.value, 2)),
    ],
)
def test_comparison_with_tuple(version_str, compare_tuple):
    v = UnityVersion.from_str(version_str)
    # eq
    assert (v == compare_tuple) == (v.as_tuple() == compare_tuple)
    # ne
    assert (v != compare_tuple) == (v.as_tuple() != compare_tuple)
    # lt
    assert (v < compare_tuple) == (v.as_tuple() < compare_tuple)
    # le
    assert (v <= compare_tuple) == (v.as_tuple() <= compare_tuple)
    # gt
    assert (v > compare_tuple) == (v.as_tuple() > compare_tuple)
    # ge
    assert (v >= compare_tuple) == (v.as_tuple() >= compare_tuple)


@pytest.mark.parametrize(
    "version_str, other_str",
    [
        ("2018.1.1f2", "2018.1.1f2"),
        ("2018.1.1f2", "2018.1.1f1"),
        ("2018.1.1f2", "2018.1.2f2"),
        ("2018.1.1f2", "2018.2.1f2"),
    ],
)
def test_comparison_with_unityversion(version_str, other_str):
    v1 = UnityVersion.from_str(version_str)
    v2 = UnityVersion.from_str(other_str)
    assert (v1 == v2) == (v1.as_tuple() == v2.as_tuple())
    assert (v1 != v2) == (v1.as_tuple() != v2.as_tuple())
    assert (v1 < v2) == (v1.as_tuple() < v2.as_tuple())
    assert (v1 <= v2) == (v1.as_tuple() <= v2.as_tuple())
    assert (v1 > v2) == (v1.as_tuple() > v2.as_tuple())
    assert (v1 >= v2) == (v1.as_tuple() >= v2.as_tuple())


def test_repr_and_str():
    v = UnityVersion.from_str("2018.1.1f2")
    assert "UnityVersion" in repr(v)
    assert str(v.major) in repr(v)
    assert str(v.minor) in repr(v)
    assert v.type_str in repr(v)
    assert str(v.type_number) in repr(v)
