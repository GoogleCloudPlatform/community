#
# Install required packages
#
apt update -y
apt install git bzip2 libgl1-mesa-glx -y

#
# Create a jupyter user and switch to that context
#
adduser jupyter --uid 2001 --disabled-password --gecos "" --quiet

#
# Install Anaconda
#
cd /tmp
wget https://repo.anaconda.com/archive/Anaconda3-5.2.0-Linux-x86_64.sh
bash Anaconda3-5.2.0-Linux-x86_64.sh -b -p /opt/anaconda3

#
# Create a Jupyter configuration or the jupyter user
#
cd /home/jupyter
mkdir .jupyter
git clone https://github.com/JuliaComputing/JuliaBoxTutorials.git notebooks

