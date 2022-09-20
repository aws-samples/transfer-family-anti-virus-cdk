import aws_cdk as core
import aws_cdk.assertions as assertions

from workflow.workflow_stack import WorkflowStack

# example tests. To run these tests, uncomment this file along with the example
# resource in workflow/workflow_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WorkflowStack(app, "workflow")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
