#!/bin/bash
#flagging
SETUP_FLAG_FILE="./.setup.flag"
LINUX_PROGRAMS_FLAG_FILE="./.linux_programs.flag"
PYTHON_MODULES_FLAG_FILE="./.python_modules.flag"
## setup stuff
if true; then
	sudo sed -i '22d' /etc/sysctl.d/10-ptrace.conf
	echo "kernel.yama.ptrace_scope = 0" |  sudo tee -a /etc/sysctl.d/10-ptrace.conf > /dev/null
else 
	echo "Environment variables already set up - if things aren't working, remember to run 'source $HOME/.profile'"
fi
echo '--------------------------------------------------------------------------------'
assert_file_exists() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo "File ${file_path} does not exist. file=${BASH_SOURCE[0]}, line=$LINENO, function=${FUNCNAME[1]}, caller=${FUNCNAME[0]}"
        exit 1
    fi
}

assert_dir_exists() {
    local dir_path="$1"
    if [ ! -d "$dir_path" ]; then
        echo "Directory ${dir_path} does not exist. file=${BASH_SOURCE[0]}, line=$LINENO, function=${FUNCNAME[1]}, caller=${FUNCNAME[0]}"
        exit 1
    fi
}

original_dir=$(pwd)

echo "Installing Linux programs..."
if true; then
    sudo apt-get -y update
    sudo apt-get -y upgrade

    packages=(
    build-essential autoconf automake libbz2-dev
    liblzma-dev libcurl4-gnutls-dev libssl-dev cmake git
    libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev
    libswscale-dev libopencv-dev libtbb-dev jq libconfig++-dev
    parallel cppcheck coinor-libipopt-dev libgtk-3-dev
    libv4l-dev libxvidcore-dev libx264-dev libjpeg-dev
    libpng-dev libtiff-dev gfortran openexr htop
    libatlas-base-dev python3-dev libtbb2 libdc1394-22-dev
    git-lfs clang-format scons libconfig-dev libhdf5-dev
    libelf-dev software-properties-common libbsd-dev
    )

    sudo apt-get install -y "${packages[@]}"
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt install -y python3.8
else
    echo "Linux programs are already installed"
fi

echo '--------------------------------------------------------------------------------'

echo "Installing Python modules..."
if true; then
    python_modules=(numpy pandas pybind11 columnar)

    if command -v pip3 &> /dev/null; then
        echo "pip is already installed"
    else
        echo "pip is not installed on this system. Installing..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3.8 get-pip.py
    fi

    pip3.8 install "${python_modules[@]}"
else
    echo "Python modules are already installed"
fi

echo '--------------------------------------------------------------------------------'

echo "Installing ZSim..."

if [[ ! -d /users/ngaertne/CNC/zsim ]]; then
    git clone https://github.com/s5z/zsim.git
    zspath=$(realpath zsim)
    echo "ZSim is already installed in $zspath"
    echo "To (re)compile zsim, wait for the script to finish executing then cd into zsim folder and run 'scons -j16'"
    echo "To run a test program, cd to the zsim folder and run './build/opt/zsim tests/simple.cfg'"
else
    zspath=$(realpath zsim)
    echo "ZSim is already installed in $zspath"
    echo "To (re)compile zsim, wait for the script to finish executing then cd into zsim folder and run 'scons -j16'"
    echo "To run a test program, cd to the zsim folder and run './build/opt/zsim tests/simple.cfg'"
fi

echo '--------------------------------------------------------------------------------'

echo "Installing Intel Pin..."
if [ -z "$PINPATH" ]; then
    pin_url="https://software.intel.com/sites/landingpage/pintool/downloads/pin-2.14-71313-gcc.4.4.7-linux.tar.gz"
    pin_dir="${pin_url##*/}"
    pin_dir="${pin_dir%%.tar.gz}"

    curl -L "$pin_url" -o pin.tar.gz
    tar -xzf pin.tar.gz
    rm pin.tar.gz
    if [[ ! -d "$pin_dir" ]]; then
       echo "$pin_dir is not created!"
        exit 1
    fi

    echo "export PINPATH=$(readlink -f $pin_dir)" >> $HOME/.bashrc
    echo "Run the following command to apply changes across all sessions."
    echo "source ~/.bashrc"
    echo "Remember to reboot after first installing pin. Use the web interface, rebooting using the console command tends to cause issues"
else
    echo "Pin is already installed. PINPATH=$PINPATH"
    echo "Remember to reboot after first installing pin. Use the web interface, rebooting using the console command tends to cause issues"
fi

echo '--------------------------------------------------------------------------------'

echo "Installing DRAMSim2..."
if [ -z "$DRAMSIMPATH" ]; then
    git clone https://github.com/umd-memsys/DRAMSim2.git
    cd DRAMSim2
    make DEBUG=1
    make libdramsim.so
    echo "export DRAMSIMPATH=$HOME/DRAMSim2" >> $HOME/.bashrc
    echo "Run the following command to apply changes across all sessions."
    echo "source ~/.bashrc"
else
    echo "DRAMSim2 is already installed. DRAMSIMPATH=$DRAMSIMPATH"
fi

echo "PLEASE RUN 'source $HOME/.profile'"
echo "If this is your first time running this script, please also reboot using the web interface - some system-level vars need to be refreshed and doing so using the console has caused issues"
