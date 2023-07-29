#
# Start the notebook server
#
cat <<JUPYTER_SERVICE > /lib/systemd/system/jupyter.service
[Unit]
Description=Jupyter notebook server
After=network.target

[Service]
ExecStart=/opt/anaconda3/bin/jupyter notebook \
    --config=/home/jupyter/.jupyter/jupyter_notebook_config.py \
    --no-browser \
    --port=8089 \
    --notebook-dir=/home/jupyter/notebooks

User=jupyter
Group=jupyter

Restart=no
PrivateTmp=true
ProtectSystem=true

[Install]
WantedBy=multi-user.target
JUPYTER_SERVICE

systemctl enable juypter.service
systemctl daemon-reload
systemctl restart jupyter.service

