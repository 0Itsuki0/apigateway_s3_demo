import aws_cdk as core
import aws_cdk.assertions as assertions

from apigateway_s3_fileupload.apigateway_s3_fileupload_stack import ApigatewayS3FileuploadStack

# example tests. To run these tests, uncomment this file along with the example
# resource in apigateway_s3_fileupload/apigateway_s3_fileupload_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ApigatewayS3FileuploadStack(app, "apigateway-s3-fileupload")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
