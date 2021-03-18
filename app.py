#!.env/bin/python

from aws_cdk import core

import stacks

env = core.Environment(account="473883619336", region="us-east-1")

app = core.App()

stacks.Production(app, "blog-backend-production-stack", env=env)
stacks.Testing(app, "blog-backend-testing-stack", env=env)

app.synth()
