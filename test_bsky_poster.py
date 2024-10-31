from bsky_poster import *

def test_get_hashtags():
    assert get_hashtags("#MyHouseInUmbria #RichardLoncraine #MaggieSmith #ChrisCooper #RonnieBarker") == ['MyHouseInUmbria', 'RichardLoncraine', 'MaggieSmith', 'ChrisCooper', 'RonnieBarker']
    assert get_hashtags(" Some rubbish here with some #hashtags and other #interesting stuff") == ['hashtags', 'interesting']
        

