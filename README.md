# Blog backend

Built on AWS with API Gateway + Lambda + DynamoDB, deployed with CDK Python.

## Structure

- lambda/proxy -> main Lambda Fn, configured as an API Gateway proxy
- core dir -> custom logic (distributed as a Lambda Layer, run build_core_layer.sh for deployment)

## Deployment

(domain name and certificate are set up manually -> AWS Route53, AWS CM)

1. $ cdk synth
2. $ cdk bootstrap
3. $ cdk deploy