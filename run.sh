#!/bin/bash

export PYTHONUNBUFFERED=true

./ead-html-validator.py -d Omega-EAD.xml ~/omega/guides/tamwag/mos_2021/ 2>&1 | tee out.log

