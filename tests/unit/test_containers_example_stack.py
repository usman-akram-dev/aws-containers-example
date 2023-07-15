import aws_cdk as core
import aws_cdk.assertions as assertions

from code.containers_example_stack import ContainersExampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in containers_example/containers_example_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ContainersExampleStack(app, "containers-example")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
