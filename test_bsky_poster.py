from bsky_poster import *

def test_get_hashtags():
    description = "Photo of the day: Sitting on Ramses II's feet\nMortuary Temple of Pharaoh Ramesses II, Luxor, Egypt (1991)\n #Egypt #Luxor #Photography"
    assert get_hashtags(description) == [{'index': {'byteStart': 107, 'byteEnd': 113}, 'features': [{'$type': 'app.bsky.richtext.facet#tag', 'tag': 'Egypt'}]}, {'index': {'byteStart': 114, 'byteEnd': 120}, 'features': [{'$type': 'app.bsky.richtext.facet#tag', 'tag': 'Luxor'}]}, {'index': {'byteStart': 121, 'byteEnd': 133}, 'features': [{'$type': 'app.bsky.richtext.facet#tag', 'tag': 'Photography'}]}]
        
# def test_get_did(mocker):
#    mock_data = {"did": "did:plc:wiyfnlefs2t477yqngjcls4r"}
#
#    mock_response = mocker.MagicMock()
#    mock_response.json.return_value = mock_data
#
#    print(mock_response.json.return_value)
#    mocker.patch("requests.get", return_value=mock_response)
#
#    result = get_did("handle.bsky.social")
#    result = mock_data    
#    assert type(result) is dict
#    assert result["did"] == "did:plc:wiyfnlefs2t477yqngjcls4r"

