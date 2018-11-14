cat <<JUPYTER_CONFIG > /home/jupyter/.jupyter/jupyter_notebook_config.py
c.NotebookApp.certfile = u'/home/jupyter/nbcert.pem'
c.NotebookApp.keyfile = u'/home/jupyter/nbkey.key'
c.NotebookApp.allow_origin = '*'
c.NotebookApp.ip = '*'
c.NotebookApp.port = 8089
c.NotebookApp.password = u'HASHED_PASSWD'
JUPYTER_CONFIG

chown jupyter -R /home/jupyter

