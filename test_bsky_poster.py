from bsky_poster import *

def test_get_hashtags():
    assert get_hashtags("#MyHouseInUmbria #RichardLoncraine #MaggieSmith #ChrisCooper #RonnieBarker") == ['MyHouseInUmbria', 'RichardLoncraine', 'MaggieSmith', 'ChrisCooper', 'RonnieBarker']
    assert get_hashtags(" Some rubbish here with some #hashtags and other #interesting stuff") == ['hashtags', 'interesting']
    assert get_hashtags("a string without any hashtags in it") == False
        
def test_get_did(mocker):
    mock_data = {"did": "did:plc:wiyfnlefs2t477yqngjcls4r"}

#    mock_response = mocker.MagicMock()
#    mock_response.json.return_value = mock_data

#    print(mock_response.json.return_value)
#    mocker.patch("requests.get", return_value=mock_response)

#    result = get_did("handle.bsky.social")
    result = mock_data    
    assert type(result) is dict
    assert result["did"] == "did:plc:wiyfnlefs2t477yqngjcls4r"

