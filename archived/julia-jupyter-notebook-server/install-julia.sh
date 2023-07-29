#
# Install Julia
#
cd /opt
mkdir julia
cd julia
wget https://julialang-s3.julialang.org/bin/linux/x64/1.0/julia-1.0.0-linux-x86_64.tar.gz
tar zxf julia-1.0.0-linux-x86_64.tar.gz
rm julia-1.0.0-linux-x86_64.tar.gz
ln -s /opt/julia/julia-1.0.0/bin/julia /usr/local/bin

#
# Add the Julia kernel to the Jupyter setup
#
cat <<IJULIA > /tmp/ijulia.jl
using Pkg
Pkg.add("IJulia")
IJULIA

chown jupyter /tmp/ijulia.jl
su - jupyter -c 'julia /tmp/ijulia.jl'
rm /tmp/ijulia.jl
