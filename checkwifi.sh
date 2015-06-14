ping -c4 192.168.181.1 > /dev/null

if [ $? == 0 ]
then
   echo "Network connected, nothing to do..."
   exit
fi

echo "No network connection, restarting wlan0"
/sbin/ifdown 'wlan0'
sleep 5
/sbin/ifup --force 'wlan0'

sleep 5

ping -c4 192.168.181.1 > /dev/null

if [ $? == 0 ]
then
   echo "Network back!"
fi

echo "Still no network connection, rebooting"
sudo /sbin/shutdown -r now
