# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
FROM --platform=linux/amd64  amazon/aws-lambda-python:3.9

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}

# Copy freshclam configuration
COPY freshclam.conf ${LAMBDA_TASK_ROOT}/freshclam.conf

RUN yum -y install clamav && \
    freshclam --config-file=${LAMBDA_TASK_ROOT}/freshclam.conf --stdout --datadir=${LAMBDA_TASK_ROOT}/database

CMD [ "app.lambda_handler" ]