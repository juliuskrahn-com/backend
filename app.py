#!.env/bin/python

from aws_cdk import core

import stacks

env = core.Environment(account="473883619336", region="us-east-1")

app = core.App()

stacks.Production(app, "production", env=env)
stacks.Testing(app, "testing", env=env)

app.synth()
