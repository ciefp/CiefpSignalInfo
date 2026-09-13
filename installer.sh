#!/bin/bash
##setup command=wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpSignalInfo/main/installer.sh -O - | /bin/sh

######### Only This 2 lines to edit with new version ######
version='1.5'
changelog='\nAdded DVB-T/T2 support\nAdded Mini Skin with channel navigation\nAdded Satfinder integration\nAdded local PiconManager\nAdded Channel number for DVB-T'
##############################################################

# Check if we should skip restart (for batch installations)
SKIP_REBOOT="${SKIP_REBOOT:-0}"

TMPPATH=/tmp/CiefpSignalInfo

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/CiefpSignalInfo
fi

# check depends packages
if [ -f /var/lib/dpkg/status ]; then
   STATUS=/var/lib/dpkg/status
   OSTYPE=DreamOs
else
   STATUS=/var/lib/opkg/status
   OSTYPE=Dream
fi
echo ""
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "You have Python3 image"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "You have Python2 image"
    PYTHON=PY2
    Packagerequests=python-requests
fi

if [ $PYTHON = "PY3" ]; then
    if grep -qs "Package: $Packagesix" $STATUS ; then
        echo ""
    else
        opkg update && opkg install python3-six
    fi
fi
echo ""
if grep -qs "Package: $Packagerequests" $STATUS ; then
    echo ""
else
    echo "Need to install $Packagerequests"
    echo ""
    if [ $OSTYPE = "DreamOs" ]; then
        apt-get update && apt-get install python-requests -y
    elif [ $PYTHON = "PY3" ]; then
        opkg update && opkg install python3-requests
    elif [ $PYTHON = "PY2" ]; then
        opkg update && opkg install python-requests
    fi
fi
echo ""

## Remove tmp directory
[ -d $TMPPATH ] && rm -rf $TMPPATH > /dev/null 2>&1

## Remove old plugin directory
[ -d $PLUGINPATH ] && rm -rf $PLUGINPATH

# Download and install plugin
mkdir -p $TMPPATH
cd $TMPPATH
set -e

if [ -f /var/lib/dpkg/status ]; then
   echo "# Your image is OE2.5/2.6 #"
   echo ""
else
   echo "# Your image is OE2.0 #"
   echo ""
fi

# Download latest release
wget --no-check-certificate https://github.com/ciefp/CiefpSignalInfo/archive/refs/heads/main.tar.gz
tar -xzf main.tar.gz

# Copy files to correct location
# Ova linija radi samo ako repo ima strukturu: CiefpSignalInfo-main/usr/lib/enigma2/...
if [ -d "CiefpSignalInfo-main/usr" ]; then
    cp -r 'CiefpSignalInfo-main/usr' '/'
else
    # Fallback: ako repo ima fajlove direktno u root-u
    echo "Using flat structure..."
    mkdir -p $PLUGINPATH
    cp -r CiefpSignalInfo-main/* $PLUGINPATH/
fi

set +e
cd
sleep 2

### Check if plugin installed correctly
if [ ! -d $PLUGINPATH ]; then
    echo "Something wrong .. Plugin not installed"
    exit 1
fi

# Provera da li su glavni fajlovi tu
if [ ! -f "$PLUGINPATH/CiefpSignalInfo.py" ]; then
    echo "ERROR: CiefpSignalInfo.py not found!"
    exit 1
fi

if [ ! -f "$PLUGINPATH/CiefpSignalInfoMini.py" ]; then
    echo "WARNING: CiefpSignalInfoMini.py not found (mini skin may not work)"
fi

if [ ! -d "$PLUGINPATH/components" ]; then
    echo "WARNING: components folder not found (picon manager may not work)"
fi

rm -rf $TMPPATH > /dev/null 2>&1
sync
echo ""
echo ""
echo "#########################################################"
echo "#        CiefpSignalInfo v$version INSTALLED            #"
echo "#                  developed by ciefp                   #"
echo "#                  .::CiefpSettings::.                  #"
echo "#               https://github.com/ciefp                #"
echo "#########################################################"

# Only restart if SKIP_REBOOT is not set to 1
if [ "$SKIP_REBOOT" = "0" ]; then
    echo "#           your Device will RESTART Now                #"
    echo "#########################################################"
    sleep 5
    killall -9 enigma2
else
    echo "#        Restart skipped (batch installation)           #"
    echo "#########################################################"
fi

exit 0