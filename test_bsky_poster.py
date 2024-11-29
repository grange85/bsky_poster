from bsky_poster_new import *

description1 = "Photo of the day: Sitting on Ramses II's feet\nMortuary Temple of Pharaoh Ramesses II, Luxor, Egypt (1991)\n #Egypt #Luxor #Photography"
description2 = "#192: Dean & Britta - Crystal Blue RIP (Füxa remix)\nThis was a split single with Füxa from 2011 released on fab UK indie (and long time Füxa champions) Rocket... #Fuxa #MyRecordCollection #DeanAndBritta https://media.fullofwishes.co.uk/00-misc/ahfow-web/ahfow-2015-site-image1400x1400.jpg more stuff"
description3 = "#192: Dean & Britta - Crystal Blue RIP (Füxa remix)\nThis was a split single with Füxa from 2011 released on fab UK indie (and long time Füxa champions) Rocket... #Fuxa #MyRecordCollection #DeanAndBritta https://media.fullofwishes.co.uk/00-misc/ahfow-web/ahfow-2015-site-image1400x1400.jpg"

description4 = "My record collection: Progress report #4 (151 - 200)\nPosts 151 to 200\n #MyRecordCollection"

def test_get_hashtags():
    assert get_hashtags(description2) == {'MyRecordCollection': [171, 190], 'Fuxa': [165, 170], 'DeanAndBritta': [191, 205]}
    assert get_hashtags(description4) == {'MyRecordCollection': [71, 90]}

def test_get_url():
    assert get_url(description2) == {'https://media.fullofwishes.co.uk/00-misc/ahfow-web/ahfow-2015-site-image1400x1400.jpg': [206, 291]}
    assert get_url(description3) == {'https://media.fullofwishes.co.uk/00-misc/ahfow-web/ahfow-2015-site-image1400x1400.jpg': [206, 291]}
    assert get_url(description4) == False
        
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

