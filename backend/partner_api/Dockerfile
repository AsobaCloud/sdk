FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY lambda_handler.py auth.py validators.py rate_limit.py "${LAMBDA_TASK_ROOT}/"

CMD [ "lambda_handler.lambda_handler" ]
