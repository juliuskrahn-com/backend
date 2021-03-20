#!/bin/bash
# working dir has to be project root

cdk synth testing
cdk deploy testing
