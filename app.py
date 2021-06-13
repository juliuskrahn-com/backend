from aws_cdk import core

import stacks

app = core.App()

stacks.Production(app, "Production", env=core.Environment(account="473883619336", region="eu-central-1"))

stacks.Testing(app, "Testing", env=core.Environment(account="473883619336", region="eu-central-1"))

app.synth()
