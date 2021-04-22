from signing.signing import sign_via_app_step_1


def test_sign_via_app_step_1(transactional_db):
    assert sign_via_app_step_1("") == {'known': False}
