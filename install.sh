#! /bin/bash

#PORT=""
#USER=""
HOST=""
DST=""

function Usage {
    echo "Usage: ./install.sh --help " &&
    echo "       ./install.sh [directory]" &&
    echo "       The default install directory is ~/placement, where ~ is your home directory" && 
    echo "       The install directory is created if necessary" && exit 1
}

# Call Usage
[ "$1" = "--help" ] && Usage

# Install top directory defaults to home directory
DST=${2-$(cd; pwd -P)}/placement

echo DST=$DST

BIN="$DST/bin"
LIB="$DST/lib"
ETC="$DST/etc"

SRC=.

echo "Now installing placement..."
[ ! -d $BIN ] && (mkdir -p $BIN || exit 1)
[ ! -d $LIB ] && (mkdir -p $LIB || exit 1)
[ ! -d $ETC ] && (mkdir -p $ETC || exit 1)

for f in hardware.py architecture.py exception.py tasksbinding.py scatter.py compact.py running.py utilities.py matrix.py printing.py placement.py
do
  cp $SRC/lib/$f $LIB
done

for f in placement.conf-dist documentation.txt
do
  cp $SRC/etc/$f $ETC
done

cp $SRC/bin/placement-dist $BIN
chmod -R a=rX,u+w $LIB $BIN $ETC
chmod a+rx $BIN/placement-dist $LIB/placement.py

# edit placement-dist 
sed -i -e "s!PLACEMENT_LIB!$LIB!" $BIN/placement-dist
sed -i -e "s!PLACEMENT_ETC!$ETC!" $BIN/placement-dist

echo "That's all for me, folks !"
echo
echo "Now, you should do: "
echo "     cp $BIN/placement-dist in/a/directory/of/the/path/placement"
echo "     EDIT THE FILE to be sure all is OK (the python version for example)"
echo ""
echo "     cp $ETC/placement.conf-dist $ETC/placement.conf"
echo "     EDIT THE FILE to configure placement"



