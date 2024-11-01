from bsky_poster import *

def test_get_hashtags():
    assert get_hashtags("#MyHouseInUmbria #RichardLoncraine #MaggieSmith #ChrisCooper #RonnieBarker") == ['MyHouseInUmbria', 'RichardLoncraine', 'MaggieSmith', 'ChrisCooper', 'RonnieBarker']
    assert get_hashtags(" Some rubbish here with some #hashtags and other #interesting stuff") == ['hashtags', 'interesting']
        
def test_get_did(mocker):
    mock_data = {"did":"did:plc:wiyfnlefs2t477yqngjcls4r"}

    mock_response = mocker.MagicMock()
    mock_response.json.return_value = mock_data

#    mocker.patch("urllib3.PoolManager", return_value = mock_response.json.return_value)
    mocker.patch("urllib3.PoolManager", return_value = mock_data)

    result = get_did("handle.bsky.social")

    #assert result == json.loads(mock_data.data["did"])
    #assert type(result) is dict
    #assert result == "did:plc:wiyfnlefs2t477yqngjcls4r"

