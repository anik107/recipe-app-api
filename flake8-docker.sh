#!/bin/bash
sudo docker compose run --rm app sh -c "python -m flake8 \$@"
