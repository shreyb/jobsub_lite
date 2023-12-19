import os
import sys

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


@pytest.mark.unit
def test_getRole():
    res = fake_ifdh.getRole()
    assert res == fake_ifdh.DEFAULT_ROLE


@pytest.mark.unit
def test_getRole_override():
    override_role = "Hamburgler"
    res = fake_ifdh.getRole(override_role)
    assert res == override_role


class TestCheckToken:
    @pytest.mark.unit
    def test_bad_bearer_token_file(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "thispathdoesnotexist")
        group = "fermilab"
        assert not fake_ifdh.checkToken(group)

    @pytest.mark.unit
    def test_good(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fermilab"
        assert fake_ifdh.checkToken(group)

    @pytest.mark.unit
    def test_wrong_group(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fakegroup"
        with pytest.raises(ValueError, match="wrong group"):
            fake_ifdh.checkToken(group)

    @pytest.mark.unit
    def test_expired_token(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/expired.token")
        group = "fermilab"
        try:
            with pytest.raises(ValueError, match="expired"):
                fake_ifdh.checkToken(group)
        except jwt.ExpiredSignatureError:
            pass


class TestCheckTokenNotExpired:
    @pytest.mark.unit
    def test_fail(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/expired.token")
        try:
            token = scitokens.SciToken.discover(insecure=True)
            assert not fake_ifdh.checkToken_not_expired(token)
        except jwt.ExpiredSignatureError:
            pass

    @pytest.mark.unit
    def test_success(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        token = scitokens.SciToken.discover(insecure=True)
        assert fake_ifdh.checkToken_not_expired(token)


class TestCheckTokenRightGroupAndRole:
    @pytest.mark.unit
    def test_good(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_no_groups(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/no_groups.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(TypeError, match="wlcg\.groups"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_malformed_groups(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/malformed.token")
        group = "fermilab"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(TypeError, match="malformed.*list"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_bad_group(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "badgroup"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(ValueError, match="wrong group"):
            fake_ifdh.checkToken_right_group_and_role(token, group)

    @pytest.mark.unit
    def test_bad_role(clear_bearer_token_file, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN_FILE", "fake_ifdh_tokens/fermilab.token")
        group = "fermilab"
        role = "newrole"
        token = scitokens.SciToken.discover(insecure=True)
        with pytest.raises(ValueError, match="wrong group or role"):
            fake_ifdh.checkToken_right_group_and_role(token, group, role)


@pytest.mark.unit
def test_getToken_good(clear_token, fermilab_token):
    assert os.path.exists(fermilab_token)


@pytest.mark.unit
def test_getToken_fail(clear_token):
    with pytest.raises(PermissionError):
        os.environ["GROUP"] = "bozo"
        fake_ifdh.getToken("Analysis")


# TODO tests to add for getToken
# BEARER_TOKEN_FILE is set to good token
# BEARER_TOKEN_FILE is set to bad token (fails because it's expired) - raise correct ValueError
# BEARER_TOKEN_FILE is set to bad token (fails because it's for wrong group) - raise correct ValueError
# BEARER_TOKEN_FILE is set to token that doesn't exist - We should generate a new token - make sure it's there


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
