README
------

This is still beta software.

The ssl certificates that are provided are intended for demo purposes only.  
Please use openssl to generate your own, you can find tools online to do this
as well.

As with any project documentation is key, there is plenty more to go in here and
it will hopefully be soon!

Config:
Please see the alarmserver-example.cfg and rename to alarmserver.cfg and
customize to requirements.

Dependencies:
On windows, pyOpenSSL is required.
http://pypi.python.org/pypi/pyOpenSSL

REST API Info
-------------

*/api*

* Returns a JSON dump of all currently known states
 
*/api/alarm/arm*

* Quick arm

*/api/alarm/armwithcode?alarmcode=1111*

* Arm with a code
  * Required param = **alarmcode**

*/api/alarm/stayarm*

* Stay arm, no code needed

*/api/alarm/disarm*

* Disarm system
   * Optional param = **alarmcode**
   * If alarmcode param is missing the config file value is used instead

*/api/pgm*

* Activate a PGM output:
  * Required param = **pgmnum**
  * Required param = **alarmcode**

*/api/refresh*

* Refrseh data from alarm panel

*/api/config/eventtimeago* 

* Unknown?
  
