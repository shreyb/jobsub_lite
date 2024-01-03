import os
import pathlib
import shutil
import sys
import tempfile

import pytest
import jwt
import scitokens

#
# we assume everwhere our current directory is in the package
# test area, so go ahead and cd there
#
os.chdir(os.path.dirname(__file__))


#
# import modules we need to test, since we chdir()ed, can use relative path
# unless we're testing installed, then use /opt/jobsub_lite/...
#
if os.environ.get("JOBSUB_TEST_INSTALLED", "0") == "1":
    sys.path.append("/opt/jobsub_lite/lib")
else:
    sys.path.append("../lib")

import fake_ifdh


@pytest.fixture
def clear_token():
    if os.environ.get("BEARER_TOKEN_FILE", None):
        if os.path.exists(os.environ["BEARER_TOKEN_FILE"]):
            try:
                os.unlink(os.environ["BEARER_TOKEN_FILE"])
            except:
                pass
        del os.environ["BEARER_TOKEN_FILE"]


@pytest.fixture
def fermilab_token(clear_token):
    os.environ["GROUP"] = "fermilab"
    return fake_ifdh.getToken("Analysis")


@pytest.mark.unit
def test_getTmp():
    if os.environ.get("TMPDIR", None):
        del os.environ["TMPDIR"]
    res = fake_ifdh.getTmp()
    assert res == "/tmp"


@pytest.mark.unit
def test_getTmp_override():
    os.environ["TMPDIR"] = "/var/tmp"
    res = fake_ifdh.getTmp()
    assert res == "/var/tmp"


@pytest.mark.unit
def test_getExp_GROUP():
    os.environ["GROUP"] = "samdev"
    res = fake_ifdh.getExp()
    assert res == "samdev"


# Various getRole tests


@pytest.fixture
def stage_existing_default_role_files(set_group_fermilab):
    # If we already have a default role file, stage it somewhere else
    staged_temp_files = {}

    uid = os.getuid()
    group = os.environ.get("GROUP")
    filename = f"jobsub_default_role_{group}_{uid}"
    file_locations = ["/tmp", f'{os.environ.get("HOME")}/.config']
    try:
        for file_location in file_locations:
            file_dir = pathlib.Path(file_location)
            filepath = file_dir / filename

            if os.path.exists(filepath):
                old_file_temp = tempfile.NamedTemporaryFile(delete=False)
                os.rename(filepath, old_file_temp.name)
                staged_temp_files[filepath] = old_file_temp.name

        yield

    finally:
        # Put any staged files back
        for filepath, staged_file in staged_temp_files.items():
            os.rename(staged_file, filepath)


@pytest.mark.parametrize("file_location", ["/tmp", f'{os.environ.get("HOME")}/.config'])
@pytest.mark.unit
def test_getRole_from_default_role_file(
    file_location, stage_existing_default_role_files
):
    uid = os.getuid()
    group = os.environ.get("GROUP")
    filename = f"jobsub_default_role_{group}_{uid}"
    file_dir = pathlib.Path(file_location)
    file_dir.mkdir(exist_ok=True)
    filepath = file_dir / filename
    try:
        filepath.write_text("testrole")
        assert fake_ifdh.getRole_from_default_role_file() == "testrole"
    finally:
        os.unlink(filepath)


@pytest.mark.unit
def test_getRole_from_default_role_file_none(stage_existing_default_role_files):
    assert not fake_ifdh.getRole_from_default_role_file()


@pytest.mark.unit
def test_getRole_from_valid_token(monkeypatch):
    monkeypatch.setenv(
        "BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab_production.token"
    )
    assert fake_ifdh.getRole_from_valid_token() == "Production"


@pytest.mark.unit
def test_getRole_from_valid_token_invalid(monkeypatch):
    monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/malformed.token")
    with pytest.raises(TypeError, match="malformed.*list"):
        fake_ifdh.getRole_from_valid_token()


@pytest.mark.unit
def test_getRole_from_valid_token_none(monkeypatch):
    monkeypatch.delenv("BEARER_TOKEN_FILE", raising=False)
    assert not fake_ifdh.getRole_from_valid_token()


@pytest.mark.unit
def test_getRole(set_group_fermilab):
    res = fake_ifdh.getRole()
    assert res == fake_ifdh.DEFAULT_ROLE


@pytest.mark.unit
def test_getRole_override():
    override_role = "Hamburgler"
    res = fake_ifdh.getRole(override_role)
    assert res == override_role


@pytest.mark.parametrize(
    "token_location, preserve_or_reverse_func",
    [
        ("fake_ifdh_tokens/fermilab.token", lambda x: x),
        ("thispathdoesntexist", lambda x: not x),
        ("fake_ifdh_tokens/expired.token", lambda x: not x),
    ],
)
@pytest.mark.unit
def test_checkToken_bool(
    token_location, preserve_or_reverse_func, monkeypatch, clear_bearer_token_file
):
    monkeypatch.setenv("BEARER_TOKEN_FILE", token_location)
    group = "fermilab"
    # If we want to assert False in one of these cases, flip the result using preserve_or_reverse_func
    assert preserve_or_reverse_func(fake_ifdh.checkToken(group))


@pytest.mark.unit
def test_checkToken_wrong_group_raises(monkeypatch, clear_bearer_token_file):
    monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
    group = "fakegroup"
    with pytest.raises(ValueError, match="wrong group"):
        fake_ifdh.checkToken(group)


class TestCheckTokenNotExpired:
    @pytest.mark.unit
    def test_fail(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/expired.token")
        try:
            token = scitokens.SciToken.discover(insecure=True)
            assert not fake_ifdh.checkToken_not_expired(token)
        except jwt.ExpiredSignatureError:
            pass

    @pytest.mark.unit
    def test_success(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        token = scitokens.SciToken.discover(insecure=True)
        assert fake_ifdh.checkToken_not_expired(token)


class TestCheckTokenRightGroupAndRole:
    @pytest.mark.unit
    def test_good(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_no_groups(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/no_groups.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(TypeError, match="wlcg\.groups"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_malformed_groups(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/malformed.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(TypeError, match="malformed.*list"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_bad_group(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "badgroup"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(ValueError, match="wrong group"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_bad_role(self, clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fermilab"
        role = "newrole"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(ValueError, match="wrong group or role"):
            fake_ifdh.checkToken_right_group_and_role(token, group, role)


class TestGetToken:
    @pytest.mark.unit
    def test_good(self, clear_token, fermilab_token):
        assert os.path.exists(fermilab_token)

    @pytest.mark.unit
    def test_fail(self, monkeypatch, clear_token):
        monkeypatch.setenv("GROUP", "bozo")
        with pytest.raises(PermissionError):
            fake_ifdh.getToken("Analysis")

    @pytest.mark.unit
    def test_bearer_token_file_good(self, monkeypatch, clear_bearer_token_file):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        assert fake_ifdh.getToken() == os.environ["BEARER_TOKEN_FILE"]

    @pytest.mark.unit
    def test_bearer_token_file_expired(
        self, monkeypatch, tmp_path, clear_bearer_token_file
    ):
        # Since the token is expired, a new, valid token should show up at BEARER_TOKEN_FILE
        token_path = tmp_path / "expired.token"
        shutil.copy("fake_ifdh_tokens/expired.token", token_path)
        monkeypatch.setenv("BEARER_TOKEN_FILE", str(token_path))
        monkeypatch.setenv("GROUP", "fermilab")
        assert fake_ifdh.getToken()

    @pytest.mark.unit
    def test_bearer_token_file_wrong_group(self, monkeypatch, clear_bearer_token_file):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        monkeypatch.setenv("GROUP", "bogus")
        with pytest.raises(ValueError, match="wrong group"):
            fake_ifdh.getToken()

    @pytest.mark.unit
    def test_bearer_token_file_malformed(self, monkeypatch, clear_bearer_token_file):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/malformed.token")
        monkeypatch.setenv("GROUP", "fermilab")
        with pytest.raises(TypeError, match="malformed"):
            fake_ifdh.getToken()

    @pytest.mark.unit
    def test_bearer_token_file_not_exist(self, monkeypatch, clear_bearer_token_file):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "thisfiledoesnotexist")
        monkeypatch.setenv("GROUP", "fermilab")
        token_file = fake_ifdh.getToken()
        assert os.path.exists(token_file)


class TestGetProxy:
    @pytest.mark.unit
    def test_getProxy_good(check_user_kerberos_creds, clear_token):
        os.environ["GROUP"] = "fermilab"
        proxy = fake_ifdh.getProxy("Analysis")
        assert os.path.exists(proxy)

    @pytest.mark.unit
    def test_getProxy_override(
        check_user_kerberos_creds, clear_x509_user_proxy, clear_token, tmp_path
    ):
        fake_path = tmp_path / "test_proxy"
        os.environ["X509_USER_PROXY"] = str(fake_path)
        os.environ["GROUP"] = "fermilab"
        proxy = fake_ifdh.getProxy("Analysis")
        assert proxy == str(fake_path)

    @pytest.mark.unit
    def test_getProxy_fail(
        check_user_kerberos_creds, clear_x509_user_proxy, clear_token, tmp_path
    ):
        fake_path = tmp_path / "test_proxy"
        if os.path.exists(fake_path):
            try:
                os.unlink(fake_path)
            except:
                pass
        os.environ["X509_USER_PROXY"] = str(fake_path)
        os.environ["GROUP"] = "bozo"
        with pytest.raises(PermissionError):
            fake_ifdh.getProxy("Analysis")


@pytest.mark.unit
def test_cp():
    dest = __file__ + ".copy"
    fake_ifdh.cp(__file__, dest)
    assert os.path.exists(dest)
    os.unlink(dest)


@pytest.mark.parametrize(
    "input, expected",
    [
        (["/fermilab"], ("fermilab", "Analysis")),
        (["/fermilab/production", "/fermilab"], ("fermilab", "production")),
        (["/hypot"], ("hypot", "Analysis")),
    ],
)
@pytest.mark.unit
def test_get_group_and_role_from_token_claim_good(input, expected):
    assert fake_ifdh.get_group_and_role_from_token_claim(input) == expected


@pytest.mark.unit
def test_get_group_and_role_from_token_claim_malformed():
    input = ["hypot"]
    with pytest.raises(ValueError, match="wlcg\.groups.*token.*malformed"):
        fake_ifdh.get_group_and_role_from_token_claim(input)
