#!.env/bin/python

from aws_cdk import core

from stack import Stack

ENV = core.Environment(account="473883619336", region="us-east-1")

app = core.App()

Stack(app, "blog-backend-stack", env=ENV)

app.synth()
