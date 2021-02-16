"""Test cases for the __main__ module."""
from PIL import Image


def test_script_succeeds(responses_nwsradar, script_runner, tmp_path) -> None:
    result = script_runner.run("pynwsradar", "klwx", "radar.gif", cwd=tmp_path)
    assert result.success
    tmp_file = tmp_path / "radar.gif"
    assert tmp_file.is_file()
    with Image.open(tmp_file) as image:
        assert image.size == (800, 800)
        assert image.n_frames == 1
        assert not image.is_animated


def test_script_succeeds_num(responses_nwsradar, script_runner, tmp_path) -> None:
    result = script_runner.run(
        "pynwsradar", "--num", "2", "klwx", "radar.gif", cwd=tmp_path
    )
    assert result.success
    tmp_file = tmp_path / "radar.gif"
    assert tmp_file.is_file()
    with Image.open(tmp_file) as image:
        assert image.size == (800, 800)
        assert image.is_animated
        assert image.n_frames == 2


def test_script_succeeds_layer(
    responses_nwsradar_bdsa, script_runner, tmp_path
) -> None:
    result = script_runner.run(
        "pynwsradar", "--layer", "bdsa", "klwx", "radar.gif", cwd=tmp_path
    )
    assert result.success
    tmp_file = tmp_path / "radar.gif"
    assert tmp_file.is_file()
    with Image.open(tmp_file) as image:
        assert image.size == (800, 800)
        assert not image.is_animated
        assert image.n_frames == 1


def test_script_fails_one_arg(script_runner) -> None:
    """It exits with a status code of one."""
    result = script_runner.run("pynwsradar", "klwx")
    assert not result.success
