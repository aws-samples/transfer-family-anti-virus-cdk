import aws_cdk as core
import aws_cdk.assertions as assertions

from auth.auth_stack import AuthStack

# example tests. To run these tests, uncomment this file along with the example
# resource in auth/auth_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AuthStack(app, "auth")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
