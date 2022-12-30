import aws_cdk as core
import aws_cdk.assertions as assertions

from build.build_stack import BuildStack

# example tests. To run these tests, uncomment this file along with the example

def test_build_stack_created():
    app = core.App()
    stack = BuildStack(app, "build")
    template = assertions.Template.from_stack(stack)

