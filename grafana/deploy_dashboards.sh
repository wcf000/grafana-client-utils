#!/bin/bash

# Sync provisioning files to Grafana
rsync -avz --delete .grafana/provisioning/ /etc/grafana/provisioning/

# Restart Grafana to apply changes
systemctl restart grafana-server
