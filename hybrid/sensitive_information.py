
from typing import List


# personally identifiable information known a priori
# this is duplicated in Snapshot.java
# mint_mobile_SIM_id, nexus_6_IMEI, serial #, advertising ID, Wifi Mac Address, Bluetooth mac address, google account email, google account password
personally_identifiable_information: List[str] = ["8901240197155182897", "355458061189396", "ZX1H22KHQK", "b91481e8-4bfc-47ce-82b6-728c3f6bff60", "f8:cf:c5:d1:02:e8", "f8:cf:c5:d1:02:e7", "tester.sefm@gmail.com", "Class-Deliver-Put-Earn-5"] 



# TODO: eventually, we may need to look at some dynamic observations for more information on sensitive information strings